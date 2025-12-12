"""
Utils to load, download and save a BeautifulSoup soup containing a wikipedia html page.

Also, utils to extract paragraph text and links from a soup.
"""

import os
import requests
import pickle
import bs4
from __init__ import SOUPS_PATH, HEADERS


class WikiPage:
    """
    Represents a single Wikipedia page, including methods to download,
    parse, and extract links and paragraphs.
    """
    def __init__(self, page_name: str, lang: str = 'en'):
        self.page_name = page_name
        self.lang = lang
        self.soup = None
        self.paragraphs = []
        self.shortdescription = None
        self.url = None
        self.load()

    def load(self):
        self.url = self.get_html_url()
        self.soup = self.get_soup()
        self.paragraphs = self.get_paragraphs_text()
        self.shortdescription = self.get_shortdescription()

    def __repr__(self):
        return f"<WikiPage {self.page_name}>"

    def get_html_url(self):
        return (
            f'https://api.wikimedia.org/core/v1/wikipedia/'
            f'{self.lang}/page/{self.page_name}/html'
        )
        
    def get_soup(self) -> bs4.BeautifulSoup:
        "Given a page name, either load the saved soup or download the soup."
        fn = f'{self.page_name}.pkl'
        if fn in os.listdir(SOUPS_PATH):
            with open(os.path.join(SOUPS_PATH, fn), "rb") as f:
                soup = pickle.load(f)
        else:
            soup = self.download_soup()
        return soup

    def download_soup(self) -> bs4.BeautifulSoup:
        "Given a page name, request a wikipedia url and return the parsed html page as a bs4 soup."
        response = requests.get(self.url, headers=HEADERS, timeout=180)
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        return soup

    def save_soup(self) -> None:
        "Save the soup as a binary file."
        fn = f'{self.page_name}.pkl'
        with open(os.path.join(SOUPS_PATH, fn), "wb") as f:
            pickle.dump(self.soup, f)

    def get_shortdescription(self) -> str:
        try:
            shortdescription = self.soup.find('div', class_='shortdescription').text
        except:
            shortdescription = 'no_shortdescription'
        return shortdescription

    def get_paragraphs_text(self) -> list:
        "Return the text of all paragraphs."
        paragraphs = []
        try:
            for p in self.soup.find_all('p'):
                paragraphs.append(p.text)
        except Exception as e:
            print(str(e))
        return paragraphs

    def get_internal_page_names(self) -> list:
        """
        Extract all unique links from the page's content.
        Specifically, get all hrefs from <a> tags in <p> elements.
        """
        # List of characters or words to ignore when collecting page names
        exclude = ['#', '%', ':', '=', 'File:', 'Help:', 'List_of']
        hrefs = set()
        for p in self.soup.find_all('p'):
            for a in p.find_all('a'):
                try:
                    href = a.get('href')
                    if href.startswith('.') and not any(e in href for e in exclude):
                        hrefs.add(href[2:])
                except AttributeError:
                    continue
        return list(hrefs)



