# WikiNER
Wikipedia named entity graph explorer

## Goals
- Practice NLP. Named entity recognition, graph theory, clustering, text analysis, topic modeling, term recognition, vector search and DBs.
- Practice data analysis. Dataset building, crawling, APIs, database schemas.
- Practice web dev. Graph visualization, product development, design.
- Learn about lexical search and combine semantic + lexical

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

- TODO: work on NER extraction (years, names, orgs, places)

### Database

The database migration is complete, transitioning the project from a file-based storage system (CSV and NPY files) to a centralized SQLite database. This milestone establishes a robust foundation for data management and analysis.

**Key Achievements:**
- Successfully migrated page metadata, content (soups), and paragraph corpus from flat files.
- Unified relationship mapping (previously in CSV) within the relational schema.
- Integrated vector storage for embeddings, enabling efficient semantic search.

**Benefits of SQLite vs CSV/Files:**
- **Data Integrity:** Foreign key constraints ensure consistent relationships across pages, soups, and links.
- **Improved Performance:** Proper indexing replaces linear file scans, allowing for rapid querying of complex entity networks.
- **Simplified Versioning:** Eliminates the complexity of timestamp-based file naming and synchronization.
- **Scalability:** Provides a structured environment that can scale from local SQLite to larger systems like PostgreSQL if needed.

### Next steps

**Relationship extraction:**
- Should extend the corpus database as first-class entities
- Enables queryable relationships without file synchronization issues

### Database properties

**Schema:**
- `pages`: id (PK), name (unique), lang_code, url, crawled_at, sim_score
- `soups`: id (PK), page_id (FK), soup_data (BLOB)
- `paragraph_corpus`: id (PK), page_id (FK), text, embedding (BLOB/array), position
- `page_links`: id (PK), source_page_id (FK), target_page_id (FK)
- `page_langs`: id (PK), page_id (FK), langs

### Classes <> tables

Each class should produce a table for the DB

- Crawler → pages, soups
- CorpusManager → paragraphs/embeddings
- RelationshipBuilder → relationships


### See also

- Wikipedia Core REST API
https://api.wikimedia.org/wiki/Core_REST_API

- Wikitext
https://en.wikipedia.org/wiki/Help:Wikitext
