"""wiki api client."""

from utils import *
import pandas as pd
from rich import print
from build_network_graph import draw_graph_pyvis


def crawl():
    page_names = get_page_names()
    page_names_unrelated = get_page_names_unrelated()[:2]
    visited = set()
    for page_name in page_names:
        for new_page_name in get_paraphraphs_refs(get_soup(page_name)):
            exc = set(page_names + list(visited) + page_names_unrelated)
            if new_page_name in exc:
                continue
            else:
                soup = get_html_soup(new_page_name)
                paragraphs = get_paragraphs_text(soup)
                paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
                sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
                if sim_score >= .475:
                    save_new_page_name(new_page_name, soup, paragraphs, paragraphs_embedding)
                else:
                    with open('data/txt/page_names_unrelated.txt', 'a') as fa:
                        fa.write(new_page_name+'\n')
                visited.add(new_page_name)
                
