"""
Builds the paragraph corpus, embedding corpus, and saves to the database.
"""

import pandas as pd
import numpy as np
import sqlite3
import torch
from sentence_transformers.util import community_detection
from __init__ import DB_NAME, MODEL, logger
from wiki_page import WikiPage


class CorpusManager:
    """
    The CorpusManager handles building and managing the Wikipedia paragraph corpus
    from the database. It can load paragraphs and metadata, convert to a dataframe suitable
    for downstream processing, and keep track of corpus and embedding arrays.

    Key responsibilities:
        - Build the paragraph-level corpus from existing pages and paragraphs in the DB.
        - Load and access the corpus as structured data (e.g., Pandas DataFrame).
        - Prepare/coordinate corpus embeddings.
        - Provide convenient access to the main corpus and its properties.

    - sim_threshold (float): Minimum similarity score for included pages.
    - corpus: List of (page_id, page_name, text, position) tuples.
    - corpus_embedding: Numpy array of embeddings for each paragraph.
    - df: DataFrame view of the corpus.

    Usage:
        cm = CorpusManager(sim_threshold=0.4)
        cm.load()
        df = cm.df
        embeddings = cm.corpus_embedding
    """
    def __init__(self, sim_threshold: float = .45):
        self.sim_threshold = sim_threshold
        self.corpus = None
        self.corpus_embedding = None
        self.df = None
        self.load()

    def load(self) -> pd.DataFrame:
        self._build()
        self.corpus = self._read()
        self.df = self._to_df()
        self._load_corpus_embedding()
        assert self.df.shape[0] == self.corpus_embedding.shape[0]

    def _read(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT paragraph_corpus.id, page_id, pages.name, text, position, pages.lang_code
            FROM paragraph_corpus
            LEFT JOIN pages ON paragraph_corpus.page_id = pages.id
        """)
        corpus = cur.fetchall()
        logger.info(f'Read paragraphs with {len(corpus)} rows')
        return corpus

    def _load_corpus_embedding(self):
        """
        Load all paragraph embeddings from the database and stack them into a numpy array.

        This method fetches the binary embeddings from the `embedding` column in the
        `paragraph_corpus` table, converts each to a float32 numpy array, and stacks
        them vertically to produce a 2D array representing the corpus.

        Sets:
            self.corpus_embedding (np.ndarray): An array of shape (num_paragraphs, embedding_dim).
        """
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""SELECT embedding FROM paragraph_corpus""")
        embeddings = [np.frombuffer(e[0], dtype=np.float32) for e in cur.fetchall()]
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
        logger.info(f'{len(pages)} page_ids in pages table with sim_score > {self.sim_threshold}')
        if len(pages) == 0:
            raise ValueError(f'No pages found with sim_score > {self.sim_threshold}')
        conn.close()
        return pages

    def _get_corpus_page_ids(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""SELECT page_id FROM paragraph_corpus""")
        pc_page_ids = cur.fetchall()
        pc_page_ids = set([p[0] for p in pc_page_ids])
        logger.info(f'{len(pc_page_ids)} page_ids in paragraph_corpus table')
        return pc_page_ids

    def _build(self):
        """
        From the pages table, get the pages with sim_score >= self.sim_threshold
        and not in the paragraph_corpus table.
        For each page, create a WikiPage object and save the paragraphs to the database.
        """
        logger.info('Building corpus...')
        pages = self._get_pages_table()
        pc_page_ids = self._get_corpus_page_ids()
        # iterate over page ids and save paragraphs
        n = 0
        for page_id, page_name, lang_code, _ in pages:
            if page_id not in pc_page_ids:
                wp = WikiPage(page_name, lang_code=lang_code)
                paragraphs = wp.paragraphs
                if len(paragraphs) > 0:
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
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

    def similarity_search(self, query: str, top_k_min: int=500) -> pd.DataFrame:
        """
        Given a query, retrieve corpus rows that resemble the query.
        Return the results in a dataframe, sorted by descending similarity.
        """
        # embeddings
        corpus_embeddings = self.corpus_embedding
        query_embedding = MODEL.encode_query(query)

        # similarity scores
        similarity_scores = MODEL.similarity(query_embedding, corpus_embeddings)[0]
        top_k = min(top_k_min, len(self.df))
        scores, indices = torch.topk(similarity_scores, k=top_k)

        # similar rows
        rows = []
        for score, idx in zip(scores, indices):
            row = self.df.iloc[int(idx)]
            row['score'] = float(score)
            rows.append(row)

        # dataframe
        df = pd.DataFrame(rows).reset_index(drop=True)
        df = df.sort_values(by='score', ascending=False)
        logger.info(f'returned query results with shape {df.shape}')
        return df

    def get_top_pages(df_sim: pd.DataFrame, top_n: int=20) -> list[str]:
        "group similarity df by page name and calculate paragraph similarity average"
        # todo: deduplicate page names
        df_sim = df_sim.drop(columns=['paragraphs'])
        df_sim_grouped = df_sim.groupby('page_name', as_index=False)['score'].mean()
        df_sim_grouped = df_sim_grouped.sort_values(by='score', ascending=False)
        df_sim_grouped = df_sim_grouped[:top_n]
        top_pages = df_sim_grouped['page_name'].to_list()
        logger.info(f'returned {len(top_pages)} top_pages')
        return top_pages

    def get_page_group_dict(df):
        """community_detection"""
        df = df.groupby('page_name')['paragraphs'].apply(lambda paras: ' '.join(paras)).reset_index()
        corpus_embedding = MODEL.encode_document(df['paragraphs'].tolist())
        groups_lists = community_detection(corpus_embedding, min_community_size=10, threshold=.6)

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
        group_dict = {k: v for k, v in zip(dfc['page_name'], dfc['group'])}
        return group_dict