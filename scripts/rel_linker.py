"""Utils to build page relationships."""

import os
import pandas as pd
from datetime import datetime
from soup_utils import get_soup, get_internal_page_names, find_page_years, find_page_persons
from data_utils import get_page_names, csv_path

current_datetime_str = datetime.now().strftime('%Y-%m-%d-%H')


def build_page_relationships(target='year'):
    """
    Get the list of all saved page names, read them and find all their internal linked pages.
    
    Return a dataframe with these columns:
        - "source" -> str: the page name
        - "target" -> str: the relevant data from each page name
            - targets can be one of these types:
                - internal link
                - year
                - person
        - "target_freq" -> int: the overall frequency value of the targets
    todo: define a database of page relationships
    """
    page_names = get_page_names()
    print(f'Building relationships from {len(page_names)} pages...')
    
    rows = []
    for page_name in page_names:
        if target == 'page':
            new_page_names = get_internal_page_names(page_name)
            for new_page_name in new_page_names:
                rows.append((page_name, new_page_name))
        if target == 'year':
            years = find_page_years(page_name)  
            if len(years) > 0:
                for year in years:
                    rows.append((page_name, year))
        if target == 'person':
            persons = find_page_persons(page_name)  
            if len(persons) > 0:
                for person in persons:
                    rows.append((page_name, person))
            
    df = pd.DataFrame(rows)
    df.columns = ['source', 'target']
    df['target_freq'] = df['target'].map(df['target'].value_counts())
    print(f'Built {len(df)} relationships')
    save_page_relationships(df, target)
    return df


def save_page_relationships(df, target):
    fn = f'page_relationships_{target}_{current_datetime_str}.csv'
    fp = os.path.join(csv_path, fn)
    df.to_csv(fp, index=False, sep=',')
    print(f'{len(df)} relationships saved to {fp}')


def read_page_relationships(target):
    fn = f'page_relationships_{target}_{current_datetime_str}.csv'
    fp = os.path.join(csv_path, fn)
    df = pd.read_csv(fp)
    print(f'{len(df)} relationships read from {fp}')
    return df


def get_page_relationships(target):
    fn = f'page_relationships_{target}_{current_datetime_str}.csv'
    if fn in os.listdir(csv_path):
        df = read_page_relationships(target)
    else:
        df = build_page_relationships(target)
    return df
