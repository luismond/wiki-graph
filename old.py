

# # def get_wiki_rels_target_names(dfr):
# #     dfr = dfr.sort_values(by='target_freq', ascending=False)
# #     dfr_target = dfr[dfr['target_freq'] >= 1]
# #     dfr_target = dfr_target.drop_duplicates(subset='target')
# #     dfr_target = dfr_target['target'].tolist()[:50]
# #     names = [name for name in dfr_target]# if name not in dfr['source'].tolist() \
# #         #and name not in exclude and name not in seed_names]
# #     return names


# # def validate_new_page_name(new_page_name):
# #     paragraphs = get_paragraphs_text(new_page_name)[:45]
# #     paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
# #     sim_score = float(MODEL.similarity(paragraphs_embedding, seed_corpus_embedding)[0])
# #     if sim_score > .5:
# #         print(new_page_name)
# #         print(sim_score)
# #         return new_page_name


# def get_html_url(href):
#     return f'https://api.wikimedia.org/core/v1/wikipedia/{LANG}/page/{href}/html'


# def get_short_desc(soup):
#     try:
#         shortdesc = soup.find('div', class_='shortdescription').text
#     except:
#         shortdesc = 'no_shortdesc'
#     return shortdesc


# def get_wiki_names_descriptions():
#     df = pd.read_csv('data/csv/wiki_rels.csv')
#     df = df.sort_values(by='target_freq', ascending=False)
#     df_target = df[df['target_freq'] > 6]
#     tfd = dict(zip(df['target'], df['target_freq']))
#     # df['source'].tolist() +
#     names = sorted(set(df_target['target'].tolist()))
#     names = [name for name in names if name not in exclude and name not in seed_names]
#     print(len(names))

#     rows = []
#     for name in names:
#         print(name)
#         html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{name}/html'
#         soup = get_html_soup(html_url)
#         shortdesc = get_short_desc(soup)
#         rows.append((name, shortdesc))

#     df = pd.DataFrame(rows)
#     df.columns = ['name', 'shortdesc']
#     df['page_freq'] = df['name'].apply(lambda s: tfd.get(s, 0))
#     df.to_csv('data/csv/wiki_names_descs.csv', index=False, sep=',')
#     print('descriptions completed!')


# def get_wiki_names_paragraphs():
#     df = pd.read_csv('data/csv/wiki_rels.csv')[:10]
#     df_target = df[df['target_freq'] > 3]
#     tfd = dict(zip(df['target'], df['target_freq']))
#     names = set(df['source'].tolist() + df_target['target'].tolist()) 
#     print(len(names))
#     #names = ['Unidentified_flying_object', 'Ufology', 'Extraterrestrial_life',
#     #'UFO', 'Flying_saucer', 'Extraterrestrial_hypothesis']
#     rows = []
#     for name in list(names):
#         print(name)
#         html_url = f'https://api.wikimedia.org/core/v1/wikipedia/en/page/{name}/html'
#         soup = get_html_soup(html_url)
#         paragraphs = get_paragraphs_text(soup)
#         for paragraph in paragraphs:
#             try:
#                 #paragraph_embedding = model.encode_query(paragraph)
#                 #similarity_score = model.similarity(paragraph_embedding, corpus_embeddings)[0]
#                 #similarity_score_avg = sum(similarity_score) / len(similarity_score)
#                 #print(similarity_score_avg)
#                 #x = list(zip(paragraph, similarity_scores))
#                 rows.append((name, paragraph))
#             except Exception as e:
#                 print(str(e))
#                 continue
#         #paragraphs_embedding = model.encode_document(paragraphs)
#         #similarity_scores = model.similarity(paragraphs_embedding, corpus_embeddings)[0]
#         #x = list(zip(paragraphs, similarity_scores))
#         #rows.append((name, paragraphs))
#     print(len(rows))
#     df = pd.DataFrame(rows)
#     df.columns = ['name', 'paragraph']
#     #df = df.explode('paragraphs')
#     df = df[df['paragraph'].apply(lambda s: len(str(s).strip().split()) > 2)]
#     df.to_csv('data/csv/wiki_related_names_paragraphs.csv', index=False, sep='\t')
#     print('paragraphs completed!')