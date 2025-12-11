"""
Handles the collection of pages, tracks processed/unrelated pages,
and provides access to the full dataset.
"""

import os
from datetime import datetime
import pandas as pd
from random import shuffle
from wiki_page import WikiPage
from __init__ import CSV_PATH, TXT_PATH, PARAGRAPHS_PATH


page_names_file = os.path.join(TXT_PATH, 'page_names.txt')
page_names_unrelated_file = os.path.join(TXT_PATH, 'page_names_unrelated.txt')


def get_page_names(shuffled=True) -> list:
    "Get the list of page names, randomized by default."
    with open(page_names_file, 'r') as fr:
        page_names = [p.strip() for p in fr.read().split('\n')]
    if shuffled:
        shuffle(page_names)  
    return page_names


def get_page_names_unrelated() -> list:
    "Get the list of unrelated page names."
    with open(page_names_unrelated_file, 'r') as fr:
        page_names_unrelated = [p.strip() for p in fr.read().split('\n')]
    return page_names_unrelated


def append_new_page_name(page_name: str):
    "When a page has been validated and saved, add the page name to this file."
    with open(page_names_file, 'a') as fa:
        fa.write(page_name+'\n')


def append_new_unrelated_page_name(page_name: str):
    "When a page is considered irrelevant, add the page name to this file."
    with open(page_names_unrelated_file, 'a') as fa:
        fa.write(page_name+'\n')


def get_alpha_ratio(string: str) -> float:
    """
    Calculate the ratio of alphabetic characters in a string.
    """
    alpha_n = [ch for ch in string if ch.isalpha()]
    alpha_ratio = len(alpha_n) / len(string)
    return alpha_ratio 


class CorpusManager:
    def __init__(self):
        self.corpus = None
        self.current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
        self.file_name = f"corpus_{self.current_datetime_str}.tsv"
    
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
        print(f'read {self.file_name} ({corpus.shape} and {unique_pages} pages')
        return corpus

    def _build(self)-> pd.DataFrame:
        """Build a corpus from the saved pages' paragraphs."""
        print(f'Building corpus...')
        rows = []
        for fn in os.listdir(PARAGRAPHS_PATH):
            with open(os.path.join(PARAGRAPHS_PATH, fn), 'r') as f:
                c = f.read().split('\n')
            lines = [l for l in c if len(l.split()) > 5 and get_alpha_ratio(l) > .75]
            for line in lines:
                rows.append((fn[:-4], line))
        df = pd.DataFrame(rows)
        df.columns = ['page_name', 'paragraphs']
        return df

    def _save(self):
        self.corpus.to_csv(os.path.join(CSV_PATH, self.file_name), index=False, sep='\t')
        print(f'saved corpus to {self.file_name} with shape {self.corpus.shape}')




# def get_query_from_corpus(df_corpus: pd.DataFrame, query_names: list[str]) -> str:
#     "pass a list of page names to use their paragraphs as query"
#     dfq = df_corpus[df_corpus['page_name'].isin(query_names)]
#     query = ' '.join(dfq['paragraphs'].tolist())
#     return query


# def main():
#     sim_threshold = .5
#     for n in range(20):
#         print(f'crawling... ({n})')
#         crawl(sim_threshold)
#         sim_threshold *= .97
#         print(sim_threshold)

# if __name__ == "__main__":
#     main()
