"NLP utils using sentence models. Encoding, similarity, etc."

import os
import pandas as pd
import torch
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')


def get_seed_embedding():
    """
    Take the paragraphs of an initial set of pages and encode them.
    This seed embedding will be used to determine the similarity of the new crawled pages.
    """
    df = pd.read_csv('data/csv/wiki_query_names_paragraphs.csv', sep='\t')
    seed_embedding = MODEL.encode_document(' '.join(df['paragraphs'].tolist()))
    print('loaded seed embedding')
    return seed_embedding


seed_corpus_embedding = get_seed_embedding()


def save_page_embedding(page_name, paragraphs_embedding):
    """Save the paragraphs embedding with the page name."""
    np.save(f"data/embs/{page_name}.npy", paragraphs_embedding)


def save_corpus_embedding(corpus_embeddings):
    """Save the corpus embedding with the datetime."""
    current_datetime_str = datetime.now().strftime('%Y-%m-%d %H')
    corpus_fn = f"corpus_{current_datetime_str}.npy"
    np.save(f"data/embs/{corpus_fn}", corpus_embeddings)
    print(f'saved {corpus_fn}')


def load_corpus_embedding(corpus):
    """
    To avoid encoding the whole corpus each time, this function will:
    - Check the current date
    - If a corpus embedding exists with this date name, load it
    - If not, encode the corpus and save it with the current date name
    - Return the corpus embedding
    """
    current_datetime_str = datetime.now().strftime('%Y-%m-%d %H')
    corpus_fn = f"corpus_{current_datetime_str}.npy"
    if corpus_fn in os.listdir('data/embs'):
        corpus_embeddings = np.load(f'data/embs/{corpus_fn}')
        print(f'loaded {corpus_fn}')
    else:
        corpus_embeddings = MODEL.encode_document(corpus)
        print(f'encoded {corpus_fn}')
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
    corpus = df_corpus['paragraph'].tolist()
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
    df_sim = df_sim.sort_values(by='score', ascending=False)
    df_sim.to_csv('data/csv/wiki_names_paragraphs_query_results.tsv', index=False, sep='\t')
    return df_sim