"""
Handles the collection of pages, tracks processed/unrelated pages,
and provides access to the full dataset.
"""

import os
from datetime import datetime
import pandas as pd
from wiki_page import WikiPage
import numpy as np
from __init__ import CSV_PATH, SOUPS_PATH, EMBS_PATH
from nlp_utils import MODEL


def get_alpha_ratio(string: str) -> float:
    """Calculate the ratio of alphabetic characters in a string."""
    alpha_n = [ch for ch in string if ch.isalpha()]
    alpha_ratio = len(alpha_n) / len(string)
    return alpha_ratio 


class CorpusManager:
    def __init__(self):
        self.corpus = None
        self.corpus_embedding = None
        self.current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
        self.file_name = f"corpus_{self.current_datetime_str}.tsv"
        self.load()
    
    def load(self) -> pd.DataFrame:
        """
        - If a corpus exists with the date name, read it
        - If not, build the corpus and save it with the current date name
        - This also ensures that the corpus embedding and the text corpus are aligned

        """
        if self.file_name in os.listdir(CSV_PATH):
            self.corpus = self._read()
        else:
            self.corpus = self._build()
            self._save()

    def _read(self)-> pd.DataFrame:
        corpus = pd.read_csv(os.path.join(CSV_PATH, self.file_name), sep='\t')
        unique_pages = len(corpus['page_name'].unique())
        print(f'Read {self.file_name} ({corpus.shape} and {unique_pages} pages')
        return corpus

    def _build(self):
        """Build a corpus from the saved pages' paragraphs."""
        print(f'Building corpus...')
        rows = []
        for fn in os.listdir(SOUPS_PATH):
            page_name = fn[:-4]
            wp = WikiPage(page_name)
            paragraphs = wp.paragraphs
            for p in paragraphs:
                if len(p.split()) > 5 and get_alpha_ratio(p) > .75:
                    rows.append((page_name, p))
        df = pd.DataFrame(rows)
        df.columns = ['page_name', 'paragraphs']
        return df

    def _save(self):
        self.corpus.to_csv(os.path.join(CSV_PATH, self.file_name), index=False, sep='\t')
        print(f'Saved corpus to {self.file_name} with shape {self.corpus.shape}')

    def load_corpus_embedding(self):
        ce = CorpusEmbedding(self.corpus, self.current_datetime_str)
        self.corpus_embedding = ce.corpus_embedding
        return ce.corpus_embedding


class CorpusEmbedding:
    def __init__(self, corpus: pd.DataFrame, current_datetime_str: str):
        self.corpus = corpus
        self.current_datetime_str = current_datetime_str
        self.corpus_embedding = None
        self.file_name = f"corpus_{self.current_datetime_str}.npy"
        self.file_path = os.path.join(EMBS_PATH, self.file_name)
        self.load()


    def load(self) -> np.ndarray:
        """
        To avoid encoding the whole corpus each run, this function will:
        - Use the corpus date name
        - If a corpus embedding exists with this date name, load it
        - If not, encode the corpus and save it with the current date name
        - Return the corpus embedding
        # bug fix: the saved corpus embedding and the text corpus loose alignment.
        # the text corpus should need to be saved likewise

        """
        if self.file_name in os.listdir(EMBS_PATH):
            corpus_embeddings = self._read()
        else:
            corpus_embeddings = self._build()
            self._save()
        return corpus_embeddings

    def _read(self):
        corpus_embeddings = np.load(self.file_path)
        print(f'read {self.file_path} with shape {corpus_embeddings.shape}')
        return corpus_embeddings

    def _build(self):
        print(f'encoding corpus...')
        corpus_embeddings = MODEL.encode_document(self.corpus['paragraphs'])
        return corpus_embeddings

    def _save(self):
        np.save(self.file_path, self.corpus_embeddings)
        print(f'saved {self.file_name} with shape {self.corpus_embeddings.shape}')
