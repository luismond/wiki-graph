# uap-ent
Wikipedia entity graph explorer


## Goals

- Practice NLP. Named entity recognition, graph theory, clustering, text analysis, topic modeling, term recognition, vector search and DBs.

- Practice data analysis. Dataset building, crawling, APIs, database schemas.

- Practice web dev. Graph visualization, product development, design.


### WikiPage
- Represents a Wikipedia page and provides access to its content.
- Fetches raw HTML, parses, and extracts all paragraphs from the page.
- Identifies and stores internal links to other Wikipedia pages for graph/network analysis.
- Supports saving page content to disk and integrating with downstream data pipelines.
- Environment variables required:
  - `ACCESS_TOKEN`: Your Wikimedia API access token.
  - `APP_NAME`: The name of your application (for User-Agent).
  - `EMAIL`: Contact email address (for User-Agent).

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


### NetworkGraph
- Manages the corpus relationships
  - Page <> page
  - Page <> year
  - Page <> person
  - Person <> person

- Generates a network from these relationships
- Generates an interactive network graph

- issue: if source_page_id exists, how to save subsequent, different relations?
- simplify the _build method and only collect get_internal_page_names
- rethink the NER extraction (years, names, orgs, places)
- maybe in the same table or in separate tables


### Next steps


**Database migration:**
- Main goal: migrate to a proper DB (SQLite for simplicity, PostgreSQL for scale)
- Benefits: eliminates timestamp-based file naming, proper indexing, data integrity, versioning
- Migration strategy: incremental (pages (ok) → pg corpus (ok) → relationships → embeddings)

**Data normalization:**
- Avoid redundancy: timestamped corpus duplicates

**Relationship extraction:**
- Should extend the corpus database as first-class entities
- Enables queryable relationships without file synchronization issues

### Database properties

**Schema:**
- `pages`: id (PK), name (unique), url, crawled_at, sim_score
- `paragraphs`: id (PK), page_id (FK), text, position
- `relationships`: id (PK), source_page_id (FK), target (FK), target_type
- `embeddings`: paragraph_id (FK), embedding_vector (BLOB/array), model_version

### Classes <> tables

Each class should produce a table for the DB

- CorpusManager → paragraphs, embeddings
- Crawler → pages, soups
- RelationshipBuilder → relationships


### See also

- Wikipedia Core REST API
https://api.wikimedia.org/wiki/Core_REST_API

- Wikitext
https://en.wikipedia.org/wiki/Help:Wikitext
