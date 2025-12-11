"NLP utils using language models. Encoding, similarity, NER, etc."

import os
import pandas as pd
import torch
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer, community_detection
from gliner import GLiNER
from __init__ import CSV_PATH, EMBS_PATH
import warnings
warnings.filterwarnings('ignore')

MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')
# # Initialize GLiNER with the base model
# model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

def get_seed_embedding() -> np.ndarray:
    """
    Take the paragraphs of an initial set of pages and encode them.
    This seed embedding will be used to determine the similarity of the new crawled pages.
    """
    fn = os.path.join(CSV_PATH, 'seed_paragraphs.csv')
    df = pd.read_csv(fn)
    paragraphs = df['paragraphs'].tolist()
    seed_embedding = MODEL.encode(' '.join(paragraphs))
    print('loaded seed embedding')
    return seed_embedding


seed_corpus_embedding = get_seed_embedding()


def save_page_embedding(page_name: str, paragraphs_embedding: np.ndarray):
    """Save the paragraphs embedding with the page name."""
    fn = os.path.join(EMBS_PATH, f'{page_name}.npy')
    np.save(fn, paragraphs_embedding)


def save_corpus_embedding(corpus_embeddings: np.ndarray):
    """Save the corpus embedding with the datetime."""
    current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
    fn = f"corpus_{current_datetime_str}.npy"
    fp = os.path.join(EMBS_PATH, fn)
    np.save(fp, corpus_embeddings)
    print(f'saved {fn} with shape {corpus_embeddings.shape}')


def load_corpus_embedding(corpus: list[str]) -> np.ndarray:
    """
    To avoid encoding the whole corpus each run, this function will:
    - Check the current date
    - If a corpus embedding exists with this date name, load it
    - If not, encode the corpus and save it with the current date name
    - Return the corpus embedding
    # bug fix: the saved corpus embedding and the text corpus loose alignment.
    # the text corpus should need to be saved likewise

    """
    current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
    corpus_fn = f"corpus_{current_datetime_str}.npy"
    corpus_fp = os.path.join(EMBS_PATH, corpus_fn)
    if corpus_fn in os.listdir(EMBS_PATH):
        corpus_embeddings = np.load(corpus_fp)
        print(f'loaded {corpus_fn} with shape {corpus_embeddings.shape}')
    else:
        print(f'encoding {corpus_fn}...')
        corpus_embeddings = MODEL.encode_document(corpus)
        save_corpus_embedding(corpus_embeddings)
    return corpus_embeddings


def get_page_similarity_score(paragraphs: list) -> float:
    """Given a list of paragraphs, encode them and calculate their similarity against the seed."""
    paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
    sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
    return sim_score


def get_df_sim(df_corpus: pd.DataFrame, query: str, top_k_min: int=500) -> pd.DataFrame:
    """
    Given a query and a corpus, retrieve corpus rows that resemble the query.
    Return the results in a dataframe, sorted by descending similarity, and save it as tsv.
    """
    
    # embeddings
    corpus = df_corpus['paragraphs'].tolist()
    corpus_embeddings = load_corpus_embedding(corpus)
    query_embedding = MODEL.encode_query(query)

    # similarity scores
    similarity_scores = MODEL.similarity(query_embedding, corpus_embeddings)[0]
    top_k = min(top_k_min, len(df_corpus))
    scores, indices = torch.topk(similarity_scores, k=top_k)

    # similar rows
    rows = []
    for score, idx in zip(scores, indices):
        row = df_corpus.iloc[int(idx)]
        row['score'] = float(score)
        rows.append(row)

    # dataframe
    df_sim = pd.DataFrame(rows)
    df_sim = df_sim.reset_index(drop=True)
    df_sim = df_sim.sort_values(by='score', ascending=False)
    fn = f'{query[:15]}..._query_results.csv'
    fp = os.path.join(CSV_PATH, fn)
    df_sim.to_csv(fp, index=False, sep='\t')
    print(f'saved query results to {fn} with shape {df_sim.shape}')
    return df_sim


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


def get_page_group_dict(df):
    """df should be a corpus"""
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
