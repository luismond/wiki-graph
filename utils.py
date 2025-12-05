"""Utils for wiki api client."""

from config import HEADERS, LANG, MODEL
import requests
import os
from bs4 import BeautifulSoup as bs
import pandas as pd
from rich import print
import numpy as np
import pickle
from random import shuffle

# DATA
with open('data/txt/exclude.txt', 'r') as fr:
    exclude = [n.strip() for n in fr.readlines()]

with open('data/txt/seed_names.txt', 'r') as fr:
    seed_names = [n.strip() for n in fr.readlines()]


dirs = ['data/soups', 'data/embs', 'data/paragraphs']


def get_page_names():
    page_names_file = 'data/txt/page_names.txt'
    with open(page_names_file, 'r') as fr:
        page_names = [p.strip() for p in fr.read().split('\n')]
        #_, page_names = zip(*sorted(enumerate(page_names), reverse=True))  
    return page_names


def get_page_names_unrelated():
    page_names_unrelated_file = 'data/txt/page_names_unrelated.txt'
    with open(page_names_unrelated_file, 'r') as fr:
        page_names_unrelated = [p.strip() for p in fr.read().split('\n')]
    return page_names_unrelated


def get_seed_corpus_embedding():
    dfqp = pd.read_csv('data/csv/wiki_query_names_paragraphs.csv', sep='\t')
    corpus = dfqp['paragraphs'].tolist()
    print(len(corpus))
    seed_corpus_embedding = MODEL.encode_document(' '.join(corpus))
    return seed_corpus_embedding

seed_corpus_embedding = get_seed_corpus_embedding()


def get_wiki_rels_target_names(dfr):
    dfr = dfr.sort_values(by='target_freq', ascending=False)
    dfr_target = dfr[dfr['target_freq'] >= 1]
    dfr_target = dfr_target.drop_duplicates(subset='target')
    dfr_target = dfr_target['target'].tolist()[:50]
    names = [name for name in dfr_target]# if name not in dfr['source'].tolist() \
        #and name not in exclude and name not in seed_names]
    return names


def validate_new_page_name(new_page_name):
    paragraphs = get_paragraphs_text(new_page_name)[:45]
    paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
    sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
    if sim_score > .5:
        print(new_page_name)
        print(sim_score)
        return new_page_name


# HTML utils
def get_html_soup(page_name):
    html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{page_name}/html'
    response = requests.get(html_url, headers=HEADERS)
    data = response.text
    soup = bs(data, features="html.parser")
    return soup


def get_paragraphs_text(soup) -> list:
    #soup = get_html_soup(page_name)
    paragraphs = []
    try:
        for p in soup.find_all('p'):
            paragraphs.append(p.text)
    except Exception as e:
        print(str(e))
    return paragraphs
        

def get_paraphraphs_refs(soup):
    """Extract all unique internal Wiki hrefs from <a> tags in <p> elements, skipping excluded names."""
    #soup = get_html_soup(page_name)
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


def get_html_url(href):
    return f'https://api.wikimedia.org/core/v1/wikipedia/{LANG}/page/{href}/html'


def get_short_desc(soup):
    try:
        shortdesc = soup.find('div', class_='shortdescription').text
    except:
        shortdesc = 'no_shortdesc'
    return shortdesc


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


def get_soup(page_name):
    if f'{page_name}.pkl' in os.listdir('data/soups'):
        # print('loading soup')
        with open(f"data/soups/{page_name}.pkl", "rb") as f:
            soup = pickle.load(f)
        return soup
    else:
        # print('fetching soup')
        return get_html_soup(page_name)


def get_wiki_names_descriptions():
    df = pd.read_csv('data/csv/wiki_rels.csv')
    df = df.sort_values(by='target_freq', ascending=False)
    df_target = df[df['target_freq'] > 6]
    tfd = dict(zip(df['target'], df['target_freq']))
    # df['source'].tolist() +
    names = sorted(set(df_target['target'].tolist()))
    names = [name for name in names if name not in exclude and name not in seed_names]
    print(len(names))

    rows = []
    for name in names:
        print(name)
        html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{name}/html'
        soup = get_html_soup(html_url)
        shortdesc = get_short_desc(soup)
        rows.append((name, shortdesc))

    df = pd.DataFrame(rows)
    df.columns = ['name', 'shortdesc']
    df['page_freq'] = df['name'].apply(lambda s: tfd.get(s, 0))
    df.to_csv('data/csv/wiki_names_descs.csv', index=False, sep=',')
    print('descriptions completed!')


def get_wiki_names_paragraphs():
    df = pd.read_csv('data/csv/wiki_rels.csv')[:10]
    df_target = df[df['target_freq'] > 3]
    tfd = dict(zip(df['target'], df['target_freq']))
    names = set(df['source'].tolist() + df_target['target'].tolist()) 
    print(len(names))
    #names = ['Unidentified_flying_object', 'Ufology', 'Extraterrestrial_life',
    #'UFO', 'Flying_saucer', 'Extraterrestrial_hypothesis']
    rows = []
    for name in list(names):
        print(name)
        html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{name}/html'
        soup = get_html_soup(html_url)
        paragraphs = get_paragraphs_text(soup)
        for paragraph in paragraphs:
            try:
                #paragraph_embedding = model.encode_query(paragraph)
                #similarity_score = model.similarity(paragraph_embedding, corpus_embeddings)[0]
                #similarity_score_avg = sum(similarity_score) / len(similarity_score)
                #print(similarity_score_avg)
                #x = list(zip(paragraph, similarity_scores))
                rows.append((name, paragraph))
            except Exception as e:
                print(str(e))
                continue
        #paragraphs_embedding = model.encode_document(paragraphs)
        #similarity_scores = model.similarity(paragraphs_embedding, corpus_embeddings)[0]
        #x = list(zip(paragraphs, similarity_scores))
        #rows.append((name, paragraphs))
    print(len(rows))
    df = pd.DataFrame(rows)
    df.columns = ['name', 'paragraph']
    #df = df.explode('paragraphs')
    df = df[df['paragraph'].apply(lambda s: len(str(s).strip().split()) > 2)]
    df.to_csv('data/csv/wiki_related_names_paragraphs.csv', index=False, sep='\t')
    print('paragraphs completed!')