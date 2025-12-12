"""
Wiki pages crawler

1. Iterate over the page names from the pages table
2. Find their internal page links and check if they are saved
3. Once a new page link is discovered, the paragraphs are extracted
4. The paragraphs are encoded and compared with a seed
5. If the similarity is above the threshold, the new page is saved as soup
6. The page name and metadata are saved in the pages table
"""

import os
import pandas as pd
from wiki_page import WikiPage
from nlp_utils import get_page_similarity_score
from __init__ import current_datetime_str, pages_fp
from datetime import datetime



def append_new_page_name(page_name: str, url: str, crawled_at: str, sim_score: float):
    "When a page has been visited add the page name & metadata to this file."
    with open(pages_fp, 'a') as fa:
        fa.write(f'{page_name}\t{url}\t{crawled_at}\t{sim_score}\n')


def crawl(sim_threshold: float=0.5):
    pages = pd.read_csv(pages_fp, sep='\t')
    page_names = pages[pages['sim_score'] >= .5]['name'].tolist()
    visited = set()
    for page_name in page_names:
        wp = WikiPage(page_name)
        new_page_names = wp.get_internal_page_names()
        for new_page_name in new_page_names:
            if new_page_name in set(pages['name'].tolist() + list(visited)):
                continue
            else:
                wp_new = WikiPage(new_page_name)
                sim_score = get_page_similarity_score(wp_new.paragraphs)
                if sim_score >= sim_threshold:
                    wp_new.save_soup()
                append_new_page_name(new_page_name, wp_new.url, current_datetime_str, sim_score)
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
