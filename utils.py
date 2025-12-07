"""Utils for wiki api client."""
import os
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import pickle
from random import shuffle
from rich import print
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')
load_dotenv()


# HEADERS
def get_headers():
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    APP_NAME = os.getenv("APP_NAME")
    EMAIL = os.getenv("EMAIL")
    HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}
    return HEADERS

HEADERS = get_headers()

# MODELS
MODEL = SentenceTransformer('distiluse-base-multilingual-cased-v1')

# # LANGUAGES
# LANG = 'en'

# # DIRS
# dirs = ['data/soups', 'data/embs', 'data/paragraphs']

# # FILES
page_names_file = 'data/txt/page_names.txt'
page_names_unrelated_file = 'data/txt/page_names_unrelated.txt'
exclude_file = 'data/txt/exclude.txt'


# # DATA
def get_exclude():
    with open(exclude_file, 'r') as fr:
        return [n.strip() for n in fr.readlines()]


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


def get_seed_names():
    with open('data/txt/seed_names.txt', 'r') as fr:
        return [n.strip() for n in fr.readlines()]


def get_seed_corpus_embedding():
    dfqp = pd.read_csv('data/csv/wiki_query_names_paragraphs.csv', sep='\t')
    corpus = dfqp['paragraphs'].tolist()
    seed_corpus_embedding = MODEL.encode_document(' '.join(corpus))
    print('loaded seed_corpus_embedding')
    return seed_corpus_embedding


exclude = get_exclude()
seed_corpus_embedding = get_seed_corpus_embedding()


# HTML utils
def get_html_soup(page_name):
    html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{page_name}/html'
    response = requests.get(html_url, headers=HEADERS, timeout=60)
    data = response.text
    soup = bs(data, features="html.parser")
    return soup


def get_soup(page_name):
    #print(f'\n### reading {page_name} soup... ###')
    if f'{page_name}.pkl' in os.listdir('data/soups'):
        with open(f"data/soups/{page_name}.pkl", "rb") as f:
            soup = pickle.load(f)
        return soup
    else:
        return get_html_soup(page_name)


def get_paragraphs_text(soup) -> list:
    paragraphs = []
    try:
        for p in soup.find_all('p'):
            paragraphs.append(p.text)
    except Exception as e:
        print(str(e))
    return paragraphs
        

def get_paraphraphs_refs(soup):
    """Extract all unique internal Wiki hrefs from <a> tags in <p> elements, skipping excluded names."""
    hrefs = set()
    for p in soup.find_all('p'):
        for a in p.find_all('a'):
            try:
                href = a.get('href')
                if href.startswith('.') and not any(e in href for e in exclude):
                    href_ = href[2:]
                    if href_ not in exclude:
                        hrefs.add(href_)
            except AttributeError:
                continue
    return list(hrefs)


def save_new_page_name(new_page_name, soup, paragraphs, paragraphs_embedding):

    with open(f"data/soups/{new_page_name}.pkl", "wb") as f:
        pickle.dump(soup, f)
    
    with open(f"data/paragraphs/{new_page_name}.txt", "w") as f:
        f.write('\n'.join(paragraphs))
    
    np.save(f"data/embs/{new_page_name}.npy", paragraphs_embedding)
    
    page_names_file = 'data/txt/page_names.txt'
    with open(page_names_file, 'a') as fa:
        fa.write(new_page_name+'\n')
    
    print(f'!! saved {new_page_name} !!')


def get_page_relationships():
    "read all pages and return a df with the page names and all their linked page names"
    print('getting related links from all pages...')
    page_names = get_page_names()

    rows = []
    for page_name in page_names:
        soup_ = get_soup(page_name)
        new_page_names = get_paraphraphs_refs(soup_)
        for new_page_name in new_page_names:     
            rows.append((page_name, new_page_name))
    df = pd.DataFrame(rows)

    df.columns = ['source', 'target']
    df['relationship'] = 'co_occurs_with'
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    #df = df.drop_duplicates(subset=['source', 'target', 'relationship'])
    df.to_csv('data/csv/wiki_rels.csv', index=False, sep=',')
    print(f'{len(df)} relationships found and saved')
