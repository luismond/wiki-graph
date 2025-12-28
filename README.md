# wiki-graph

Wiki-graph is a toolkit for exploring Wikipedia as a structured graph of
knowledge. It provides tools to download, parse, and analyze Wikipedia
articles, extracting the network of links between pages and enabling semantic
and network-based research. With a modular system for fetching page content,
managing corpora, and visualizing connections, wiki-graph supports both data
collection (via crawling and processing) and advanced relationship analysis
(via network graphs and embeddings). The project leverages a centralized SQLite
database to store text, relationships, and vector data, making it easy to
perform scalable search, retrieval, and graph operations on Wikipedia-derived
knowledge.

Wiki-graph offers robust multilingual support, allowing users to analyze and
visualize Wikipedia content across numerous languages.
Its modular architecture can efficiently handle language-specific corpora, and
build cross-lingual relationship graphs. With integrated tools for multilingual
crawling, parsing, and storage, wiki-graph facilitates comparative studies and
knowledge discovery both within and across Wikipedia language editions.
The toolkit is designed with language-agnostic interfaces so that new languages
can be added with minimal configuration, enabling scalable multilingual
research and exploration.


## Classes

### CorpusManager
- Manages the corpus: loads and builds the paragraph corpus from wiki pages.
- Works with already-collected data
- Focused on data management/retrieval

### CorpusBitexts
- Handles extraction, alignment, and management of parallel (bitext) corpora
  from Wikipedia pages.
- Enables building multilingual corpora by aligning paragraphs and sections
  across different language editions.


### WikiPage
- Represents a Wikipedia page and provides access to its content.
- Fetches raw HTML, parses, and extracts all paragraphs from the page.
- Identifies and stores internal links to other Wikipedia pages for
  graph/network analysis.
- Supports saving page content to disk and integrating with downstream data
  pipelines.


### Crawler
- Discovers new pages by following links
- Validates pages against similarity thresholds
- Saves individual pages (metadata, content and embeddings)
- Focused on data collection/discovery

### PagesGraph
- Manages the graph of interlinked pages
- Generates a network from these relationships

## SQLite database
The database serves as the central storage for all Wikipedia data collected,
processed, and analyzed by wiki-graph. It is designed to efficiently support
multilingual, large-scale storage and retrieval of Wikipedia content, including
full page data, extracted paragraphs, embeddings, internal links, and
cross-lingual alignments.

The schema is organized around the key entities managed by each main class:
pages, page content, paragraph-level corpora, inter-page links, and available
languages per page. By separating these aspects, the database enables fast
queries for network analysis, retrieval of text for NLP tasks, and scalable
additions of new languages or relationships.

All data ingestion—from crawling, parsing, graph-building, to multilingual
bitext alignment—is persisted in normalized relational tables.
This sets the foundation for downstream tasks such as relationship extraction,
named entity recognition, visualization, semantic search, and cross-lingual
comparison, making the toolkit flexible for both research and applied
data science purposes.


### Database schema

- `pages`: id (PK), name (unique), lang_code, url, crawled_at, sim_score
- `paragraph_corpus`: id (PK), page_id (FK), text, embedding (BLOB/array),
   position
- `page_links`: id (PK), source_page_id (FK), target_page_id (FK)
- `page_autonyms`: id (PK), source_page_id (FK), autonym, autonym_page_id,
   lang_code


### Known bugs

- Requests using some language codes return a forbidden status
    - While trying to crawl pages in de, fr, it, a 403 (forbidden) status code
      was received.
    - After logging in to Wikipedia, and adding the languages from the
      languages drop-down,
      the API requests for those language codes became available.

### See also

- Wikipedia Core REST API
https://api.wikimedia.org/wiki/Core_REST_API

- Wikitext
https://en.wikipedia.org/wiki/Help:Wikitext


### Environment variables
- Environment variables required:
  - `ACCESS_TOKEN`: Your Wikimedia API access token.
  - `APP_NAME`: The name of your application (for User-Agent).
  - `EMAIL`: Contact email address (for User-Agent).
