"""Utils to build page relationships."""

# import warnings
# warnings.filterwarnings('ignore')
# from rich import print

import pandas as pd
from soup_utils import get_soup, get_internal_page_names
from data_utils import get_page_names, page_relationships_file
from datetime import datetime


def get_page_relationships():
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the linked pages from each page name
        - "target_freq" -> int: the overall frequency value of the targets
    """
    
    print('Getting related links from all pages...')

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
    return df


# def read_page_relationships():
#     current_datetime_str = datetime.now().strftime('%Y-%m-%d')
#     fn = f"corpus_{current_datetime_str}.tsv"


def load_data(df, max_edges) -> pd.DataFrame:
    df = df.fillna('')
    df['relationship'] = 'co_occurs_with'
    df = df.sort_values(by='target_freq', ascending=False)
    #df = df[df['target_freq'] >= 2]
    df = pd.concat([b[:20] for (_, b) in df.groupby('source')])
    #
    return df[:max_edges]