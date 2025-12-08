"""Utils for wiki api client."""

# import warnings
# warnings.filterwarnings('ignore')
# from rich import print

import pandas as pd
from soup_utils import get_soup, get_internal_page_names
from data_utils import get_page_names

def get_page_relationships():
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the linked pages from each page name
        - "target_freq" -> int: the overall frequency value of the targets
    """
    
    print('Getting related links from all pages...')

    page_relationships_file = 'data/csv/page_relationships.csv'

    page_names = get_page_names()

    rows = []
    for page_name in page_names:
        new_page_names = get_internal_page_names(get_soup(page_name))
        for new_page_name in new_page_names:     
            rows.append((page_name, new_page_name))
    df = pd.DataFrame(rows)

    df.columns = ['source', 'target']
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    df.to_csv(page_relationships_file, index=False, sep=',')
    print(f'{len(df)} relationships found and saved to {page_relationships_file}')

