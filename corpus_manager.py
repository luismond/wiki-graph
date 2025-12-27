"""
Builds the paragraph corpus, embedding corpus, and saves to the database.
"""

import pandas as pd
import numpy as np
import torch
from sentence_transformers.util import community_detection
from __init__ import MODEL, SIM_THRESHOLD, LANG_CODES, logger
from db_util import (
    insert_paragraph, get_paragraph_embeddings, get_paragraph_corpus,
    get_pages_data, read_autonyms_data, get_paragraphs_by_page_id
    )
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
    def __init__(self):
        self.sim_threshold = SIM_THRESHOLD
        self.lang_codes = LANG_CODES
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
        corpus = get_paragraph_corpus()
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
        embeddings = get_paragraph_embeddings()
        self.corpus_embedding = np.vstack(
            [np.frombuffer(e[0], dtype=np.float32) for e in embeddings]
            )
        logger.info('Loaded embeddings.')

    def _build(self):
        """
        Get the pages with sim_threshold >= self.sim_threshold
        and not in the paragraph_corpus table.
        For each page, create a WikiPage object and save it to the database.
        """
        logger.info('Building corpus...')

        pages = []
        for lang_code in self.lang_codes:
            pages_ = get_pages_data(self.sim_threshold, lang_code)
            for p in pages_:
                pages.append(p)

        corpus = self._read()
        pc_page_ids = set(i[1] for i in corpus)

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
                insert_paragraph(page_id, paragraph, embedding, position)
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

    @staticmethod
    def get_bitext(tgt_lang) -> pd.DataFrame:
        """
        Retrieve aligned bitext data for the specified target language.

        Args:
            tgt_lang (str): Target language code (e.g., 'fr', 'de', etc.)

        Returns:
            pd.DataFrame: DataFrame with columns -
                'page_name', 'page_id', 'autonym', 'autonym_page_id',
                'lang_code', 'src_text', 'tgt_text'

        The DataFrame contains matched paragraph texts in English and their
        corresponding autonym paragraphs in the target language.
        Each row corresponds to an aligned pair based on cross-lingual
        Wikipedia autonyms data.
        """
        autonyms_data = read_autonyms_data(tgt_lang)
        df = pd.DataFrame(autonyms_data)
        df.columns = ['page_name', 'page_id', 'autonym',
                      'autonym_page_id', 'lang_code']
        df['src_text'] = df['page_id'].apply(get_paragraphs_by_page_id)
        df['tgt_text'] = df['autonym_page_id'].apply(get_paragraphs_by_page_id)
        df = df.dropna()
        df = df.reset_index(drop=True)
        return df

    def get_bitext_corpus(self) -> pd.DataFrame:
        """
        Collect aligned bitext dataframes for all target languages
        in the corpus, concatenate them into a single DataFrame,
        and return the combined bitext corpus.

        Returns:
            pd.DataFrame: DataFrame containing aligned bitext pairs
            from all languages in 'lang_codes' except for English.
        """
        dfs = []
        for lang_code in self.lang_codes:
            if lang_code == 'en':
                continue
            df_ = self.get_bitext(lang_code)
            dfs.append(df_)
        df = pd.concat(dfs)
        df = df.reset_index(drop=True)
        return df
