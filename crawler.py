import os
from random import shuffle
from wiki_page import WikiPage
from nlp_utils import get_page_similarity_score
from __init__ import TXT_PATH


page_names_file = os.path.join(TXT_PATH, 'page_names.txt')
page_names_unrelated_file = os.path.join(TXT_PATH, 'page_names_unrelated.txt')


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


def crawl(sim_threshold: float=0.5):
    """
    1. Given a list of page names, iterate over them and find their internal page links.
    2. The crawling proceeds only if the page name isn't already saved.
    3. Once a new page link is discovered, the paragraphs are extracted.
    4. The paragraphs are encoded and compared with a seed.
    5. If the similarity is above the threshold, the new page is saved as soup and text.
    6. If the similarity is below, the page name is saved in the "unrelated pages" file.
    todo: replace txt pages with a csv with columns:
        page_name: str, saved: bool, fetch_date: str, similarity: float

    """
    page_names = get_page_names()
    page_names_unrelated = get_page_names_unrelated()
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
                sim_score = get_page_similarity_score(wp_new.paragraphs)
                if sim_score >= sim_threshold:
                    wp_new.save()
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
