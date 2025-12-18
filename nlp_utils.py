"NLP utils using language models. Encoding, similarity, NER, etc."

# import pandas as pd
# from sentence_transformers.util import community_detection
# from gliner import GLiNER
# from __init__ import logger, MODEL

# # Initialize GLiNER with the base model
# model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")

# def get_page_group_dict(df):
#     """df should be a corpus"""
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
