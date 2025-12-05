"""wiki api client."""

from config import MODEL
from utils import *
import pandas as pd
from rich import print
from build_network_graph import draw_graph_pyvis


def crawl():
    page_names = get_page_names()
    shuffle(page_names)  
    page_names_unrelated = get_page_names_unrelated()

    for page_name in page_names:
        visited = set()
        print(f'\n### reading {page_name} ###')
        soup_ = get_soup(page_name)
        new_page_names = get_paraphraphs_refs(soup_)
        for new_page_name in new_page_names:
            exc = set(page_names + list(visited) + page_names_unrelated)
            if new_page_name in exc:
                continue
            else:
                soup = get_html_soup(new_page_name)
                paragraphs = get_paragraphs_text(soup)
                paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
                sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
                if sim_score >= .5:
                    save_new_page_name(new_page_name, soup, paragraphs, paragraphs_embedding)
                else:
                    with open('data/txt/page_names_unrelated.txt', 'a') as fa:
                        fa.write(new_page_name+'\n')
                visited.add(new_page_name)
                
        
def mine_relationships():
    page_names = get_page_names()

    rows = []
    for page_name in page_names:
        soup_ = get_soup(page_name)
        new_page_names = get_paraphraphs_refs(soup_)
        for new_page_name in new_page_names:     
            rows.append((page_name, new_page_name))

    if len(rows) == 0:
        raise ValueError('zero rows')

    df = pd.DataFrame(rows)
    df.columns = ['source', 'target']
    df['relationship'] = 'co_occurs_with'

    df['target_freq'] = df['target'].map(df['target'].value_counts())
    df = df.drop_duplicates(subset=['source', 'target', 'relationship'])
    df = df[df['source'].apply(lambda s: s not in exclude)]
    df = df[df['target'].apply(lambda s: s not in exclude)]
    df.to_csv('data/csv/wiki_rels.csv', index=False, sep=',')
    print(len(df))
    print('relationships completed!')


def main():
    for _ in range(3):
        crawl()
        mine_relationships() #True False
        draw_graph_pyvis(max_edges=1000)
        #get_wiki_names_descriptions()
        #get_wiki_names_paragraphs()

if __name__ == "__main__":
    main()
