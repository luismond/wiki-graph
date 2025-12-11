"""
Handles the collection of pages, tracks processed/unrelated pages, and provides access to the full dataset.
"""

import os
from datetime import datetime
import pandas as pd
from random import shuffle
from wiki_page import WikiPage
from sbert_utils import get_page_similarity_score



BASE = os.path.dirname(__file__) 
data_path = os.path.join(BASE, "..", "data")

csv_path = os.path.join(data_path, "csv")
txt_path = os.path.join(data_path, "txt")
embs_path = os.path.join(data_path, "embs")
paragraphs_path = os.path.join(data_path, "paragraphs")
soups_path = os.path.join(data_path, "soups")

page_names_file = os.path.join(txt_path, 'page_names.txt')
page_names_unrelated_file = os.path.join(txt_path, 'page_names_unrelated.txt')
page_relationships_file = os.path.join(csv_path, 'page_relationships.csv')


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

def crawl(sim_threshold: float=0.5):
    """
    1. Given a list of page names, iterate over them and find their internal page links.
    2. The crawling proceeds only if the page name isn't already saved.
    3. Once a new page link is discovered, the paragraphs are extracted.
    4. The paragraphs are encoded and compared with a seed.
    5. If the similarity is above the threshold, the new page is saved as soup and text.
    6. If the similarity is below, the page name is saved in the "unrelated pages" file.
    """
    page_names = get_page_names()
    page_names_unrelated = get_page_names_unrelated()[:2]
    visited = set()
    for page_name in page_names:
        wp = WikiPage(page_name)
        new_page_names = wp.get_internal_page_names()
        for new_page_name in new_page_names:
            exc = set(page_names + list(visited) + page_names_unrelated)
            if new_page_name in exc:
                continue
            else:
                wp_new = WikiPage(new_page_name)
                paragraphs = wp_new.paragraphs
                sim_score = get_page_similarity_score(paragraphs)
                if sim_score >= sim_threshold:
                    print(f'saving {new_page_name}...')
                    wp_new.save_soup()
                    wp_new.save_paragraphs()
                    append_new_page_name(new_page_name)
                else:
                    append_new_unrelated_page_name(new_page_name)
                visited.add(new_page_name)


def main():
    sim_threshold = .5
    for n in range(20):
        print(f'crawling... ({n})')
        crawl(sim_threshold)
        sim_threshold *= .97
        print(sim_threshold)

if __name__ == "__main__":
    main()

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
