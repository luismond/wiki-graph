
import os
from random import shuffle

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