
import pandas as pd
import numpy as np
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
    np.save(f"data/embs/{page_name}.npy", paragraphs_embedding)


def get_page_similarity_score(paragraphs):
    paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
    sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
    return sim_score