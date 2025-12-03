"""
wiki_api.py

A script to fetch and parse the HTML content of a Wikipedia page using the Wikimedia API.
Retrieves the page's HTML, extracts all paragraphs, and collects their text.

Environment Variables Required:
- ACCESS_TOKEN: Your Wikimedia API access token.
- APP_NAME: The name of your application (for User-Agent).
- EMAIL: Contact email address (for User-Agent).


Docs:

Core REST API
https://api.wikimedia.org/wiki/Core_REST_API


Wikitext
https://en.wikipedia.org/wiki/Help:Wikitext


"""

import os
import requests
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv
from time import sleep
import pandas as pd
from rich import print
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

# ENV VARS
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME")
EMAIL = os.getenv("EMAIL")
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'User-Agent': f'{APP_NAME} ({EMAIL})'}


# DATA
with open('data/exclude.txt', 'r') as fr:
    exclude = [n.strip() for n in fr.readlines()]

with open('seed_names.txt', 'r') as fr:
    seed_names = [n.strip() for n in fr.readlines()]


# HTML FUNCS
def get_html_soup(html_url):
    response = requests.get(html_url, headers=HEADERS)
    data = response.text
    soup = bs(data, features="html.parser")
    return soup


def get_paragraphs_text(soup):
    return [p.text for p in soup.find_all('p')]


def get_paraphraphs_refs(soup):
    """Extract all unique internal Wiki hrefs from <a> tags in <p> elements, skipping excluded names."""
    hrefs = set()
    for p in soup.find_all('p'):
        for a in p.find_all('a'):
            try:
                href = a.get('href')
                if href.startswith('.') and not any(e in href for e in exclude):
                    hrefs.add(href[2:])
            except AttributeError:
                continue
    return list(hrefs)


def get_html_url(href):
    return f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{href}/html'


def get_short_desc(soup):
    try:
        shortdesc = soup.find('div', class_='shortdescription').text
    except:
        shortdesc = 'no_shortdesc'
    return shortdesc


def mine_rels():
    rows = []
    for page_name in seed_names:
        sleep(.25)
        print('\n')
        print(page_name)
        html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{page_name}/html'
        soup = get_html_soup(html_url)
        new_page_names = sorted(get_paragraphs_text(soup))
        for new_page_name in new_page_names:
            rows.append((page_name, new_page_name))

    df = pd.DataFrame(rows)
    df.columns = ['source', 'target']
    df['relationship'] = 'co_occurs_with'
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    df = df.drop_duplicates(subset=['source', 'target', 'relationship'])
    df.to_csv('wiki_rels.csv', index=False, sep=',')


def get_wiki_names_descriptions():
    df = pd.read_csv('wiki_rels.csv')
    df = df[df['target_freq'] > 2]
    tfd = dict(zip(df['target'], df['target_freq']))
    names = set(df['source'].tolist() + df['target'].tolist()) 
    print(len(names))

    rows = []
    for name in names:
        sleep(.125)
        print(name)
        html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{name}/html'
        soup = get_html_soup(html_url)
        shortdesc = get_short_desc(soup)
        rows.append((name, shortdesc))

    df = pd.DataFrame(rows)
    df.columns = ['name', 'shortdesc']
    df['page_freq'] = df['name'].apply(lambda s: tfd.get(s, 0))
    df.to_csv('wiki_names_descs.csv', index=False, sep=',')


def main():
    mine_rels()
    get_wiki_names_descriptions()

if __name__ == "__main__":
    main()
