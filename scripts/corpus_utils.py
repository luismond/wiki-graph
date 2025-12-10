"Retrieving utils for similarity searches."

import os
from datetime import datetime
import pandas as pd
from data_utils import csv_path, paragraphs_path


def get_alpha_ratio(string: str) -> float:
    """
    Calculate the ratio of alphabetic characters in a string.
    """
    alpha_n = [ch for ch in string if ch.isalpha()]
    alpha_ratio = len(alpha_n) / len(string)
    return alpha_ratio 


def build_corpus()-> pd.DataFrame:
    """
    Read the page files from the paragraphs directory to build a paragraph corpus.
    """
    print(f'building corpus...')
    rows = []
    for fn in os.listdir(paragraphs_path):
        with open(os.path.join(paragraphs_path, fn), 'r') as f:
            c = f.read().split('\n')
        lines = [l for l in c if len(l.split()) > 5 and get_alpha_ratio(l) > .75]
        for line in lines:
            rows.append((fn[:-4], line))
    df = pd.DataFrame(rows)
    df.columns = ['page_name', 'paragraphs']
    return df


def save_corpus(corpus: pd.DataFrame, fn: str):
    corpus.to_csv(os.path.join(csv_path, fn), index=False, sep='\t')
    print(f'saved corpus to {fn} with shape {corpus.shape}')


def load_corpus() -> pd.DataFrame:
    """
    To avoid building the whole corpus each run, this function will:
    - Check the current date
    - If a corpus exists with this date name, load it
    - If not, build the corpus and save it with the current date name
    - Return the corpus 
    - This also ensures that the corpus embedding and the text corpus are aligned

    """
    current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
    fn = f"corpus_{current_datetime_str}.tsv"
    if fn in os.listdir(csv_path):
        corpus = pd.read_csv(os.path.join(csv_path, fn), sep='\t')
        unique_pages = len(corpus['page_name'].unique())
        print(f'loaded {fn} with shape {corpus.shape} and {unique_pages} unique pages')
    else:
        corpus = build_corpus()
        save_corpus(corpus, fn)
    return corpus


def get_query_from_corpus(df_corpus: pd.DataFrame, query_names: list[str]) -> str:
    "pass a list of page names to use their paragraphs as query"
    dfq = df_corpus[df_corpus['page_name'].isin(query_names)]
    query = ' '.join(dfq['paragraphs'].tolist())
    return query


def get_top_pages(df_sim: pd.DataFrame, top_n: int=20) -> list[str]:
    "group similarity df by page name and calculate paragraph similarity average"
    # todo: deduplicate page names
    df_sim = df_sim.drop(columns=['paragraphs'])
    df_sim_grouped = df_sim.groupby('page_name', as_index=False)['score'].mean()
    df_sim_grouped = df_sim_grouped.sort_values(by='score', ascending=False)
    df_sim_grouped = df_sim_grouped[:top_n]
    top_pages = df_sim_grouped['page_name'].to_list()
    print(f'returned {len(top_pages)} top_pages')
    return top_pages


# def get_page_group_dict():
#     df = load_corpus()
#     df = df.groupby('page_name')['paragraphs'].apply(lambda paras: ' '.join(paras)).reset_index()
#     corpus_embedding = MODEL.encode_document(df['paragraphs'].tolist())
#     groups_lists = community_detection(corpus_embedding, min_community_size=10, threshold=.6)

#     group_dfs = []
#     for group_n, group in enumerate(groups_lists):
#         group_rows = []
#         for row_idx in group:       
#             row = df.iloc[row_idx]
#             row['group'] = group_n
#             group_rows.append(row)
#         group_df = pd.DataFrame(group_rows)
#         group_dfs.append(group_df)

#     dfc = pd.concat(group_dfs)
#     group_dict = {k: v for k, v in zip(dfc['page_name'], dfc['group'])}
#     return group_dict
