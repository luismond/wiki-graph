"NLP utils using language models. Encoding, similarity, NER, etc."

import pandas as pd
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import community_detection
from gliner import GLiNER
from __init__ import logger

MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')
# # Initialize GLiNER with the base model
# model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

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
