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

|_ sbert_utils
  |_ wiki_page
  |_ corpus_manager
  |_ relationship_graph
    |_ crawler.py
    |_ dev.ipynb


### WikiPage
- Represents a Wikipedia page and provides access to its content.
- Fetches raw HTML, parses, and extracts all paragraphs from the page.
- Identifies and stores internal links to other Wikipedia pages for graph/network analysis.
- Supports saving page content to disk and integrating with downstream data pipelines.

### CorpusManager
- Manages the corpus: loads, builds, and saves wiki pages
- Works with already-collected data
- Focused on data management/retrieval

### Crawler
- Discovers new pages by following links
- Validates pages against similarity thresholds
- Saves individual pages (soup and paragraphs)
- Updates tracking files
- Focused on data collection/discovery


### Next steps

**File reduction:**
- ✅ Remove `paragraphs/` directory (redundant - paragraphs already in corpus TSV)
- ⚠️ Keep subdirs for now (`csv/`, `embs/`, `soups/`) during migration, but plan to eliminate them
- Consider: `soups/` may be removable if storing raw HTML/text in DB instead

**Database migration:**
- Main goal: migrate to a proper DB (SQLite for simplicity, PostgreSQL for scale)
- Benefits: eliminates timestamp-based file naming, proper indexing, data integrity, versioning
- Migration strategy: incremental (corpus → relationships → embeddings)

**Data normalization:**
- Avoid redundancy: current issues include paragraphs in both files and TSV, timestamped corpus duplicates
- Proposed schema:
  - `pages` (id, name, url, crawled_at)
  - `paragraphs` (id, page_id, text, position)
  - `embeddings` (paragraph_id, embedding_vector)
  - `relationships` (id, source_page_id, target_page_id, relationship_type, metadata)

**Relationship extraction:**
- Should extend the corpus database as first-class entities
- Enables queryable relationships without file synchronization issues

### Database properties

**Proposed schema:**
- `pages`: id (PK), name (unique), url, crawled_at, metadata
- `paragraphs`: id (PK), page_id (FK), text, position, created_at
- `embeddings`: paragraph_id (FK), embedding_vector (BLOB/array), model_version
- `relationships`: id (PK), source_page_id (FK), target_page_id (FK), relationship_type, year, url, metadata



