"""Utils to build page relationships."""

import os
import pandas as pd
from datetime import datetime
from soup_utils import get_soup, get_internal_page_names
from data_utils import get_page_names, csv_path


current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')
fn = f'page_relationships_{current_datetime_str}.csv'
fp = os.path.join(csv_path, fn)


def build_page_relationships():
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the linked pages from each page name
        - "target_freq" -> int: the overall frequency value of the targets
    """
    page_names = get_page_names()
    print(f'Building relationships from {len(page_names)} pages...')
    
    rows = []
    for page_name in page_names:
        new_page_names = get_internal_page_names(get_soup(page_name))
        for new_page_name in new_page_names:     
            rows.append((page_name, new_page_name))
    df = pd.DataFrame(rows)
    df.columns = ['source', 'target']
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    print(f'Built {len(df)} relationships')
    save_page_relationships(df)
    return df


def save_page_relationships(df):
    df.to_csv(fp, index=False, sep=',')
    print(f'{len(df)} relationships saved to {fp}')


def read_page_relationships():
    df = pd.read_csv(fp)
    print(f'{len(df)} relationships read from {fp}')
    return df


def get_page_relationships():
    if fn in os.listdir(csv_path):
        df = read_page_relationships()
    else:
        df = build_page_relationships()
    return df
