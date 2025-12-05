from sentence_transformers import SentenceTransformer
import pandas as pd
import torch

model = SentenceTransformer('distiluse-base-multilingual-cased-v1')


def get_sim_df(df, query):
    # Corpus with example documents
    rows = []
    df = df.reset_index(drop=True)
    corpus = df['paragraphs'].tolist()
    corpus_embeddings = model.encode_document(corpus)

    # Find the closest n sentences of the corpus for each query sentence based on cosine similarity
    top_k = min(500, len(corpus))

    query_embedding = model.encode_query(query)

    # We use cosine-similarity and torch.topk to find the highest n scores
    similarity_scores = model.similarity(query_embedding, corpus_embeddings)[0]
    scores, indices = torch.topk(similarity_scores, k=top_k)

    for score, idx in zip(scores, indices):
        row = df.iloc[int(idx)]
        row['score'] = float(score)
        rows.append(row)

    dfx = pd.DataFrame(rows)
    return dfx        


def main():
    query = 'ufo aliens extraterrestrial uap'.split()
    df = pd.read_csv('data/csv/wiki_names_paragraphs.csv', sep='\t')
    query_names = ['Unidentified_flying_object', 'Ufology', 'Extraterrestrial_life',
    'UFO', 'Flying_saucer', 'Extraterrestrial_hypothesis']
    dfq = df[df['name'].isin(query_names)]
    ps = dfq['paragraphs'].tolist()
    print(ps[:50])
    query = query_names#' '.join(ps)

    sim_df = get_sim_df(df, query)
    sim_df.to_csv('data/csv/wiki_names_paragraphs_query_results.csv', index=False, sep='\t')

if __name__ == "__main__":
    main()