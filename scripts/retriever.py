"Retrieving utils for similarity searches."

import os
from datetime import datetime
from sbert_utils import get_df_sim
import pandas as pd


def build_corpus()-> pd.DataFrame:
    "Read the page files from the paragraphs directory to build a paragraph corpus."
    print(f'building corpus...')
    rows = []
    for fn in os.listdir('data/paragraphs'):
        with open(f'data/paragraphs/{fn}', 'r') as f:
            c = f.read().split('\n')
        lines = [l for l in c if len(l.strip()) > 5]
        for line in lines:
            rows.append((fn[:-4], line))
    df = pd.DataFrame(rows)
    df.columns = ['page_name', 'paragraph']
    return df


def load_corpus():
    """
    To avoid building the whole corpus each run, this function will:
    - Check the current date
    - If a corpus exists with this date name, load it
    - If not, build the corpus and save it with the current date name
    - Return the corpus 
    - This also ensures that the corpus embedding and the text corpus are aligned

    """
    current_datetime_str = datetime.now().strftime('%Y-%m-%d')
    corpus_fn = f"corpus_{current_datetime_str}.tsv"
    if corpus_fn in os.listdir('data/csv'):
        corpus = pd.read_csv(f'data/csv/{corpus_fn}', sep='\t')
        print(f'loaded {corpus_fn} with shape {corpus.shape}')
    else:
        corpus = build_corpus()
        corpus.to_csv(f'data/csv/{corpus_fn}', sep='\t')
        print(f'saved corpus to {corpus_fn} with shape {corpus.shape}')
    return corpus


def get_query_from_corpus(df_corpus: pd.DataFrame, query_names: list) -> str:
    "pass a list of page names to use their paragraphs as query"
    dfq = df_corpus[df_corpus['page_name'].isin(query_names)]
    query = ' '.join(dfq['paragraph'].tolist())
    return query


def get_top_pages(df_sim, top_n=20) -> pd.DataFrame:
    "group similarity df by page name and calculate paragraph similarity average"
    # todo: deduplicate page names
    df_sim = df_sim.drop(columns=['paragraph'])
    df_sim_grouped = df_sim.groupby('page_name', as_index=False)['score'].mean()
    df_sim_grouped = df_sim.sort_values(by='score', ascending=False)
    return df_sim_grouped[:top_n]


def main():
    query_names = ['Unidentified_flying_object', 'Ufology', 'Extraterrestrial_life',
    'UFO', 'Flying_saucer', 'Extraterrestrial_hypothesis' ,'List_of_reported_UFO_sightings']

    df_corpus = load_corpus()
    query = get_query_from_corpus(df_corpus, query_names)

    df_sim = get_df_sim(df_corpus, query)
    print(df_sim.head())
    print(get_top_pages(df_sim, top_n=20))


if __name__ == '__main__':
    main()
