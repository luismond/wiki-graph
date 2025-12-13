"""
Builds the paragraph corpus, embedding corpus, and saves to the database.
"""

import os
import pandas as pd
import numpy as np
import sqlite3
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
    def __init__(self):
        self.corpus = None
        self.corpus_embedding = None
        self.load()
    
    def load(self) -> pd.DataFrame:
        self._build()
        self.corpus = self._read()

    def _read(self)-> pd.DataFrame:
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("SELECT page_id, text, position FROM paragraph_corpus")
        corpus = cur.fetchall()  # list of (page_id, paragraphs)
        logger.info(f'Read paragraph_corpus with {len(corpus)} rows')
        return corpus

    def _build(self):
        """
        Build the paragraph corpus from WikiPage objects 
        and insert into the database if not present.
        """
        logger.info(f'Building corpus...')
        conn = sqlite3.connect('uap_ent.db')
        cur = conn.cursor()
        cur.execute("SELECT id, name, sim_score FROM pages")
        pages = cur.fetchall()

        cur.execute("SELECT page_id FROM paragraph_corpus")
        pc_page_ids = cur.fetchall()  # list of page_ids stored in paragraph_corpus table
        pc_page_ids = set([p[0] for p in pc_page_ids])
        logger.info(f'{len(pc_page_ids)} page_ids in paragraph_corpus table')

        n = 0
        for page_id, page_name, sim_score in pages:
            if page_id not in pc_page_ids and sim_score >= .45:
                wp = WikiPage(page_name)
                paragraphs = [
                    p for p in wp.paragraphs if len(p.split()) > 5 \
                        and get_alpha_ratio(p) > .75]
                for pos, pg in enumerate(paragraphs):
                    cur.execute(
                        "INSERT INTO paragraph_corpus (page_id, text, position) VALUES (?, ?, ?)",
                        (page_id, pg, pos)
                        )
                    conn.commit()
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
        corpus_embedding = MODEL.encode_document(self.corpus['text'])
        return corpus_embedding

    def _save(self):
        np.save(self.file_path, self.corpus_embedding)
        logger.info(f'saved {self.file_name} with shape {self.corpus_embedding.shape}')
