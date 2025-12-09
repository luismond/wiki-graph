
from soup_utils import (
    save_soup, get_soup, get_internal_page_names, download_soup,
    get_paragraphs_text, save_paragraphs
)
from sbert_utils import get_page_similarity_score
from data_utils import get_page_names, get_page_names_unrelated, append_new_page_name, append_new_unrelated_page_name


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
    page_names_unrelated = get_page_names_unrelated()
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
                    save_soup(new_page_name, soup)
                    save_paragraphs(new_page_name, paragraphs)
                    append_new_page_name(new_page_name)
                else:
                    append_new_unrelated_page_name(new_page_name)
                visited.add(new_page_name)


def main(sim_threshold=0.4):
    for n in range(5):
        print(f'crawling... ({n})')
        crawl()

if __name__ == "__main__":
    main()
