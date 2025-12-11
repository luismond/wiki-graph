# uap-ent
hobby project to follow the uap topic

<img width="1059" height="866" alt="network_graph" src="https://github.com/user-attachments/assets/99728dad-8f79-4fed-a133-1bb37e84d2ae" />


## Goals

- Practice NLP concepts. Named entity recognition, graph theory, clustering, text analysis, topic modeling, term recognition.

- Map entity relationships within the UAP topic and related topics.

# wiki_api_client

A script to fetch and parse the HTML content of a Wikipedia page using the Wikimedia API.
Retrieves the page's HTML, extracts all paragraphs, and collects their text.

Environment Variables Required:
- ACCESS_TOKEN: Your Wikimedia API access token.
- APP_NAME: The name of your application (for User-Agent).
- EMAIL: Contact email address (for User-Agent).


## Wiki API Docs:

Core REST API
https://api.wikimedia.org/wiki/Core_REST_API


Wikitext
https://en.wikipedia.org/wiki/Help:Wikitext


## Network graph

- build_network_graph.py

- Usage:
  - python build_network_graph.py relationships.csv

- Produces:
  - network_graph.html
  
- Spreadsheet structure and formulas:
- relationship_graph.sheets
- relationships
    - source, source_role, relationship, target, target_role, year, url_title, url, source_rank
- node_attrs
    - node, role, rank
- role_colors
    - role, color

=vlookup(A2, node_attrs!A:B, 2, FALSE)


## Project structure

- The project
  -- processes wikipedia pages
  -- aggregates them into a corpus of page contents
  -- finds relationships within the corpus contents and graphs them
  -- utilizes sbert utils to arbitrate page downloads and to query the corpus

### Crawler
- Discovers new pages by following links
- Validates pages against similarity thresholds
- Saves individual pages (soup and paragraphs)
- Updates tracking files
- Focused on data collection/discovery

### CorpusManager
- Manages the corpus: loads, builds, and saves
- Works with already-collected data (paragraphs)
- Focused on data management/retrieval


|_ sbert_utils
  |_ wiki_page
  |_ corpus_manager
  |_ relationship_graph
    |_ dev.ipynb
    |_ crawler.py
