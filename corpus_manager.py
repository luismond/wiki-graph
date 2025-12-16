"""
Builds the paragraph corpus, embedding corpus, and saves to the database.
"""

import os
import pandas as pd
import numpy as np
import sqlite3
import torch
from sentence_transformers import SentenceTransformer

from __init__ import DATA_PATH, current_datetime_str, logger
from wiki_page import WikiPage

MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')


def get_alpha_ratio(string: str) -> float:
    """Calculate the ratio of alphabetic characters in a string."""
    alpha_n = [ch for ch in string if ch.isalpha()]
    alpha_ratio = len(alpha_n) / len(string)
    return alpha_ratio 


class CorpusManager:
    def __init__(self, sim_threshold: float = .45):
        self.sim_threshold = sim_threshold
        self.corpus = None
        self.corpus_embedding = None
        self.df = None
        self.load()
        
    def load(self) -> pd.DataFrame:
        self._build()
        self.corpus = self._read()
        self.corpus_embedding = self.load_corpus_embedding()
        self.df = self.to_df()

    def _read(self)-> pd.DataFrame:
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("SELECT page_id, text, position FROM paragraph_corpus")
        corpus = cur.fetchall()  # list of (page_id, paragraphs)
        logger.info(f'Read paragraph_corpus with {len(corpus)} rows')
        return corpus

    def _get_pages_table(self):
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("""
        SELECT id, name, sim_score FROM pages
        WHERE sim_score >= ?
        """, (self.sim_threshold,))
        pages = cur.fetchall()
        logger.info(f'{len(pages)} page_ids in pages table with sim_score > {self.sim_threshold}')
        if len(pages) == 0:
            raise ValueError(f'No pages found with sim_score > {self.sim_threshold}')
        conn.close()
        return pages

    def get_corpus_page_ids(self):
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("""SELECT page_id FROM paragraph_corpus""")
        pc_page_ids = cur.fetchall()
        pc_page_ids = set([p[0] for p in pc_page_ids])
        logger.info(f'{len(pc_page_ids)} page_ids in paragraph_corpus table')
        return pc_page_ids

    def _build(self):
        """
        From the pages table, get the pages with sim_score >= self.sim_threshold
        and the pages not in the paragraph_corpus table.
        For each page, create a WikiPage object and save the paragraphs to the database.
        """
        logger.info(f'Building corpus...')
        pages = self._get_pages_table()
        pc_page_ids = self.get_corpus_page_ids()

        u_pages = [p for p in pages if p[0] not in pc_page_ids]
        logger.info(f'{len(u_pages)} pages to add to corpus')

        n = 0
        for page_id, page_name, _ in pages:
            if page_id not in pc_page_ids:
                wp = WikiPage(page_name)
                if len(wp.paragraphs) > 0:
                    wp.save_paragraphs(page_id)
                    n += 1
        logger.info(f'Added {n} pages to corpus')
    
    def to_df(self):
        df = pd.DataFrame(self.corpus)
        df.columns = ['page_id', 'text', 'position']
        logger.info(f'Converted corpus to dataframe with shape {df.shape}')
        return df

    def load_corpus_embedding(self):
        df = self.to_df()
        ce = CorpusEmbedding(df)
        ce.load()
        self.corpus_embedding = ce.corpus_embedding
         
    def similarity_search(self, query: str, top_k_min: int=500) -> pd.DataFrame:
        """
        Given a query, retrieve corpus rows that resemble the query.
        Return the results in a dataframe, sorted by descending similarity.
        """
        
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


class CorpusEmbedding:
    def __init__(self, corpus: pd.DataFrame):
        self.corpus = corpus
        self.corpus_embedding = None
        self.file_name = f"corpus_{current_datetime_str}.npy"
        self.file_path = os.path.join(DATA_PATH, self.file_name)

    def load(self):
        """
        To avoid encoding the whole corpus each run, this function will:
        - Use the corpus date name
        - If a corpus embedding exists with this date name, load it
        - If not, encode the corpus and save it with the current date name
        - Return the corpus embedding
        # bug fix: the saved corpus embedding and the text corpus loose alignment.
        # the text corpus should need to be saved likewise

        """
        if self.file_name in os.listdir(DATA_PATH):
            self.corpus_embedding = self._read()
        else:
            self.corpus_embedding = self._build()
            self._save()

    def _read(self):
        corpus_embedding = np.load(self.file_path)
        logger.info(f'read {self.file_path} with shape {corpus_embedding.shape}')
        return corpus_embedding

    def _build(self):
        logger.info(f'encoding corpus...')
        from nlp_utils import MODEL
        corpus_embedding = MODEL.encode_document(self.corpus['text'])
        return corpus_embedding

    def _save(self):
        np.save(self.file_path, self.corpus_embedding)
        logger.info(f'saved {self.file_name} with shape {self.corpus_embedding.shape}')
