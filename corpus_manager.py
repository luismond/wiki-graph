"""
Builds the paragraph corpus, embedding corpus, and saves to the database.
"""

import sqlite3
import pandas as pd
import numpy as np
import torch
from sentence_transformers.util import community_detection
from __init__ import DB_NAME, MODEL, SIM_THRESHOLD, logger
from wiki_page import WikiPage


class CorpusManager:
    """
    The CorpusManager builds and manages the Wikipedia paragraph corpus
    from the database. It can load paragraphs and metadata,
    convert to a dataframe suitable for downstream processing,
    and keep track of corpus and embedding arrays.

    Key responsibilities:
        - Build the paragraph-level corpus from existing pages and paragraphs
          in the DB.
        - Load and access the corpus as structured data.
        - Prepare/coordinate corpus embeddings.
        - Provide convenient access to the main corpus and its properties.
        - Provide access to vector similarity and clustering functions.

    - sim_threshold (float): Minimum similarity score for included pages.
    - corpus: List of (page_id, page_name, text, position) tuples.
    - corpus_embedding: Numpy array of embeddings for each paragraph.
    - df: DataFrame view of the corpus.

    Usage:
        cm = CorpusManager()
        df = cm.df
        corpus_embedding = cm.corpus_embedding
    """
    def __init__(self, sim_threshold: float = SIM_THRESHOLD):
        self.sim_threshold = sim_threshold
        self.corpus = None
        self.corpus_embedding = None
        self.df = None

    def load(self):
        """Initialize the module, build the corpus and load the vectors."""
        self._build()
        self.corpus = self._read()
        self.df = self._to_df()
        self._load_corpus_embedding()
        assert self.df.shape[0] == self.corpus_embedding.shape[0]

    def _read(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT paragraph_corpus.id, page_id, pages.name, 
            text, position, pages.lang_code
            FROM paragraph_corpus
            LEFT JOIN pages ON paragraph_corpus.page_id = pages.id
        """)
        corpus = cur.fetchall()
        logger.info(f'Read paragraphs with {len(corpus)} rows')
        return corpus

    def _load_corpus_embedding(self):
        """
        Load all paragraph embeddings from the database
        and stack them into a numpy array.

        This method fetches the binary embeddings from the `embedding` column
        in the `paragraph_corpus` table, converts each to a float32 np array,
        and stacks them vertically to produce a 2D array.

        Sets:
            self.corpus_embedding (np.ndarray): 
                An array of shape (num_paragraphs, embedding_dim).
        """
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""SELECT embedding FROM paragraph_corpus""")
        embeddings = [np.frombuffer(e[0], dtype=np.float32) \
                      for e in cur.fetchall()]
        corpus_embedding = np.vstack(embeddings)
        self.corpus_embedding = corpus_embedding
        logger.info(f'Loaded embeddings with shape {corpus_embedding.shape}')

    def _get_pages_table(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
        SELECT id, name, lang_code, sim_score FROM pages
        WHERE sim_score >= ?
        """, (self.sim_threshold,))
        pages = cur.fetchall()
        logger.info(
            f'{len(pages)} page_ids in pages table '
            f'with sim_score > {self.sim_threshold}'
            )
        if len(pages) == 0:
            raise ValueError(f'No pages found with sim_threshold'
                             f' > {self.sim_threshold}')
        conn.close()
        return pages

    def _get_corpus_page_ids(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""SELECT page_id FROM paragraph_corpus""")
        pc_page_ids = cur.fetchall()
        pc_page_ids = set(p[0] for p in pc_page_ids)
        logger.info(f'{len(pc_page_ids)} page_ids in paragraph_corpus table')
        return pc_page_ids

    def _build(self):
        """
        Get the pages with sim_threshold >= self.sim_threshold
        and not in the paragraph_corpus table.
        For each page, create a WikiPage object and save it to the database.
        """
        logger.info('Building corpus...')
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        pages = self._get_pages_table()
        pc_page_ids = self._get_corpus_page_ids()

        n = 0
        for page_id, page_name, lang_code, _ in pages:
            if page_id in pc_page_ids:
                continue
            wp = WikiPage(page_name, lang_code=lang_code)
            paragraphs = wp.paragraphs
            if len(paragraphs) == 0:
                continue
            for position, paragraph in enumerate(paragraphs):
                embedding = MODEL.encode(paragraph)
                embedding = np.array(embedding, dtype=np.float32).tobytes()
                cur.execute(
                    "INSERT OR IGNORE INTO paragraph_corpus "
                    "(page_id, text, embedding, position) VALUES (?, ?, ?, ?)",
                    (page_id, paragraph, embedding, position)
                )
                conn.commit()
            n += 1
        logger.info(f'Added {n} pages to corpus')

    def _to_df(self):
        df = pd.DataFrame(self.corpus)
        df.columns = [
            'paragraph_id', 'page_id', 'page_name',
            'text', 'position', 'lang_code']
        logger.info(f'Converted corpus to dataframe with shape {df.shape}')
        return df

    def _similarity_search(self, query: str, top_k_min: int=100) -> list:
        """Given a query, retrieve similar corpus rows."""
        # todo: add lang code parameter
        # embeddings
        corpus_embeddings = self.corpus_embedding
        query_embedding = MODEL.encode_query(query)

        # similarity scores
        similarity_scores = MODEL.similarity(query_embedding,
                                             corpus_embeddings)[0]
        top_k = min(top_k_min, len(self.df))
        scores, indices = torch.topk(similarity_scores, k=top_k)

        # similar rows
        rows = []
        for score, idx in zip(scores, indices):
            row = self.df.iloc[int(idx)]
            row['score'] = float(score)
            rows.append(row)
        logger.info(f'Returned {len(rows)} rows')
        return rows

    def similarity_by_paragraphs(
            self,
            query: str,
            top_k_min: int=100
            ) -> pd.DataFrame:
        """
        Retrieve similar rows, convert to df and sort by descending similarity.
        """
        rows = self._similarity_search(query=query, top_k_min=top_k_min)
        df = pd.DataFrame(rows).reset_index(drop=True)
        df = df.sort_values(by='score', ascending=False)
        logger.info(f'Returned {len(df)} paragraphs')
        return df

    def similarity_by_pages(
            self,
            query: str,
            top_k_min: int=100
            ) -> pd.DataFrame:
        "Group by page name and calculate paragraph similarity average."
        df = self.similarity_by_paragraphs(query=query, top_k_min=top_k_min)
        dfg = df.groupby('page_name', as_index=False)['score'].mean()
        dfg = dfg.sort_values(by='score', ascending=False)
        logger.info(f'Returned {len(dfg)} pages')
        return dfg

    def cluster_by_pages(
            self,
            min_community_size=20,
            threshold=0.5
            ) -> pd.DataFrame:
        """Cluster the corpus by pages."""
        #todo: pre-save the page corpus embeddings
        df = self.df.groupby('page_name')['text'].apply(
            lambda paras: ' '.join(paras)).reset_index()
        paras_embedding = MODEL.encode_document(df['text'].tolist())

        groups_lists = community_detection(
            paras_embedding,
            min_community_size=min_community_size,
            threshold=threshold
            )

        group_dfs = []
        for group_n, group in enumerate(groups_lists):
            group_rows = []
            for row_idx in group:
                row = df.iloc[row_idx]
                row['group'] = group_n
                group_rows.append(row)
            group_df = pd.DataFrame(group_rows)
            group_dfs.append(group_df)

        dfc = pd.concat(group_dfs)
        return dfc
