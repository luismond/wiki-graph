"""Wiki pages crawler."""

from random import shuffle
import sqlite3
from wiki_page import WikiPage
from nlp_utils import get_page_similarity_score
from __init__ import current_datetime_str, logger


def process_new_page_name(new_page_name, sim_threshold):
    """
    Process a new Wikipedia page name: fetch the page, compute similarity score,
    save its metadata to the database, and store its soup if the score meets the threshold.
    
    Args:
        new_page_name (str): The name of the new Wikipedia page to process.
        sim_threshold (float): The similarity threshold for saving the page's soup.
    """
    wp_new = WikiPage(new_page_name)

    # save new_page_name in pages table
    conn = sqlite3.connect('uap_ent.db')
    cur = conn.cursor()
    cur.execute(
    "INSERT INTO pages (name, url, crawled_at, sim_score) VALUES (?, ?, ?, ?)",
    (new_page_name, wp_new.url, current_datetime_str, sim_score)
    )
    conn.commit()

    # get new_page_name id
    cur.execute("SELECT id FROM pages WHERE name = ?", (new_page_name,))
    new_page_id = cur.fetchone()[0]

    sim_score = get_page_similarity_score(wp_new.paragraphs)
    if sim_score >= sim_threshold:
        wp_new.save_soup(new_page_id)


def crawl(sim_threshold: float=0.5):
    """
    Crawl Wikipedia pages based on a similarity threshold.

    This function:
    - Connects to the database and retrieves all pages.
    - Shuffles the list of page names to randomize crawling order.
    - Iterates through each page whose similarity score is above 0.4.
    - For each such page, extracts internal Wikipedia page links (<a> inside <p> tags).
    - For every internal link not already in the database, processes it as a new page
      (fetches, computes similarity, saves metadata and soup if threshold is met).

    Args:
        sim_threshold (float): The similarity threshold above which a page's soup is saved.
    """
    logger.info(f'Crawling pages with similarity threshold {sim_threshold}')
    conn = sqlite3.connect('uap_ent.db')
    cur = conn.cursor()
    cur.execute("SELECT id, name, sim_score FROM pages")
    pages = cur.fetchall()
    page_names = [name for _, name, _ in pages]
    shuffle(page_names)
    n = 0
    for _, name, sim_score in pages:
        if sim_score > .4:
            wp = WikiPage(name)
            new_page_names = wp.get_internal_page_names()
            for new_page_name in new_page_names:
                if new_page_name in page_names:
                    continue
                else:
                    process_new_page_name(new_page_name, sim_threshold)
                    n += 1
    logger.info(f'Processed {n} new pages')
    conn.close()


def main():
    logger.info(f'Starting main...')
    sim_threshold = .3
    for _ in range(20):
        crawl(sim_threshold)
        sim_threshold *= .97
    logger.info(f'Finished main')

if __name__ == "__main__":
    main()
