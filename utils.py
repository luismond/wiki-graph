"""Utils for wiki api client."""


from random import shuffle
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
from rich import print
from soup_utils import (
    save_soup, get_soup, get_internal_page_names, download_soup,
    get_paragraphs_text, save_paragraphs
)
from sbert_utils import get_page_similarity_score

from dotenv import load_dotenv
load_dotenv()

# from build_network_graph import draw_graph_pyvis


# FILES
page_names_file = 'data/txt/page_names.txt'
page_names_unrelated_file = 'data/txt/page_names_unrelated.txt'
page_relationships_file = 'data/csv/page_relationships.csv'


# DATA
def get_page_names():
    with open(page_names_file, 'r') as fr:
        page_names = [p.strip() for p in fr.read().split('\n')]
        #_, page_names = zip(*sorted(enumerate(page_names), reverse=True))
    shuffle(page_names)  
    return page_names


def get_page_names_unrelated():
    with open(page_names_unrelated_file, 'r') as fr:
        page_names_unrelated = [p.strip() for p in fr.read().split('\n')]
    return page_names_unrelated

def append_new_page_name(page_name):
    with open(page_names_file, 'a') as fa:
        fa.write(page_name+'\n')

def append_new_unrelated_page_name(page_name):
    with open(page_names_unrelated_file, 'a') as fa:
        fa.write(page_name+'\n')


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
        new_page_names = get_internal_page_names(get_soup(page_name))
        for new_page_name in new_page_names:
            exc = set(page_names + list(visited) + page_names_unrelated)
            if new_page_name in exc:
                continue
            else:
                soup = download_soup(new_page_name)
                paragraphs = get_paragraphs_text(soup)
                sim_score = get_page_similarity_score(paragraphs)
                if sim_score >= sim_threshold:
                    save_soup(soup, new_page_name)
                    save_paragraphs(new_page_name, paragraphs)
                    append_new_page_name(new_page_name)
                else:
                    append_new_unrelated_page_name(new_page_name)
                visited.add(new_page_name)
                

def get_page_relationships():
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the linked pages from each page name
        - "target_freq" -> int: the overall frequency value of the targets
    """
    
    print('Getting related links from all pages...')
    page_names = get_page_names()

    rows = []
    for page_name in page_names:
        new_page_names = get_internal_page_names(get_soup(page_name))
        for new_page_name in new_page_names:     
            rows.append((page_name, new_page_name))
    df = pd.DataFrame(rows)

    df.columns = ['source', 'target']
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    df.to_csv(page_relationships_file, index=False, sep=',')
    print(f'{len(df)} relationships found and saved')

