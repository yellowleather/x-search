# X-Search

Local-first semantic search over your Twitter likes. Import your archive, build embeddings on your own hardware, and query the collection with a Retrieval-Augmented Generation (RAG) pipeline powered by Claude or OpenAI.

## Highlights

- **Private knowledge base** – all tweet metadata, embeddings, and FAISS indexes stay on disk.
- **Hybrid retrieval** – vector search via FAISS plus PostgreSQL full-text fallback.
- **Fast onboarding** – `main.py` installs uv, sets up a virtual environment, ensures PostgreSQL state, runs schema SQL, imports likes, generates embeddings, and launches Streamlit in one pass.
- **Extensible pipeline** – modular ingestion, embedding, scraping, and RAG components so you can replace pieces independently.

## Prerequisites

- Python 3.9 or newer
- [uv](https://github.com/astral-sh/uv) for dependency management (auto-installed by `main.py` if missing)
- PostgreSQL 15 (or compatible)
- Twitter data export containing `like.js`
- At least one LLM API key: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

## Quick Start (automated)

```bash
cp path/to/twitter_export/data/like.js inputs/twitter/data/like.js
python3 main.py --db-name xsearch --db-user xsearch_user
```

The script will:

1. Install uv if necessary.
2. Verify Python and PostgreSQL binaries are available.
3. Create the specified PostgreSQL database/user if they do not exist.
4. Copy `.env.example` to `.env` (first run) and prompt you to add API keys.
5. Create `.venv` via uv and install project dependencies.
6. Apply schema SQL (`schema/001_initial_schema.sql`).
7. Import likes if the `tweets` table is empty.
8. Build embeddings if `data/vector_store` does not exist.
9. Launch the Streamlit UI at `http://localhost:8501`.

Use `--db-name`/`--db-user` flags to target different PostgreSQL instances.

## Manual Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
# edit .env and add API keys plus any overrides
python src/database/migrate.py
```

## Import and Processing Workflow

1. **Prepare data**  
   Place `like.js` at `inputs/twitter/data/like.js`. The importer expects the standard `window.YTD.like.part0 = [...]` format.

2. **Ingest tweets**  
   ```bash
   python src/ingestion/import_likes.py
   # optional: python src/ingestion/import_likes.py --file /custom/path/like.js
   ```
   Each run upserts likes and extracts author/text metadata. Vector-store friendly metadata is stored in PostgreSQL.

3. **Generate embeddings / run batch jobs**  
   ```bash
   python src/processing/batch_processor.py --task embeddings
   python src/processing/batch_processor.py --task stats   # optional reporting
   ```
   Embeddings are stored in FAISS indexes under `data/vector_store/tweets` and `data/vector_store/links`.

4. **Start the UI**  
   ```bash
   streamlit run src/ui/app.py
   ```

## Python API Example

```python
from src.retrieval.rag_pipeline import rag_pipeline

result = rag_pipeline.query("What productivity tips keep recurring?")
print(result["answer"])
for tweet in result["sources"]["tweets"]:
    print(f"@{tweet['author_username']}: {tweet['text'][:100]}...")
```

## Configuration

All configuration lives in `.env` (loaded via `python-dotenv`). Key settings:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Credentials for answer generation (at least one required for LLM responses). |
| `DATABASE_URL` | PostgreSQL connection string. Defaults to `postgresql://xsearch_user@localhost:5432/xsearch`. |
| `TOP_K_RESULTS`, `MIN_SIMILARITY_THRESHOLD` | Retrieval tuning knobs. |
| `EMBEDDING_MODEL`, `EMBEDDING_DEVICE`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_DIMENSION` | Embedding settings passed to `sentence-transformers`. |
| `VECTOR_STORE_PATH` | Directory for FAISS indexes (`data/vector_store` by default). |
| `LLM_MODEL`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, `MAX_CONTEXT_TOKENS` | Answer generation controls. |
| `ENABLE_LINK_SCRAPING`, `ENABLE_CONTEXT_FETCHING`, `ENABLE_EMBEDDING_GENERATION` | Feature flags for optional processing stages. |
| `BATCH_SIZE`, `MAX_WORKERS`, `SCRAPING_DELAY`, `REQUEST_TIMEOUT` | General processing parameters. |

After editing `.env`, re-run import or processing scripts as needed.

## Architecture

```
Twitter like.js
   |
   |  (import_likes.py parses export, writes PostgreSQL rows)
   v
PostgreSQL (tweets, linked_content, analytics tables)
   |
   |  (embedding generator pulls pending rows)
   v
FAISS vector store on disk
   |
   |  (rag_pipeline hybrid search + LLM)
   v
Streamlit UI / Python clients
```

## Project Structure

```
x-search/
├── data/                  # Vector indexes and generated assets (gitignored)
├── inputs/twitter/data/   # Place like.js here
├── logs/
├── main.py                # Automated setup script
├── schema/
│   └── 001_initial_schema.sql
├── src/
│   ├── config/settings.py
│   ├── database/
│   │   ├── connection.py
│   │   └── migrate.py
│   ├── ingestion/
│   │   ├── import_likes.py
│   │   └── link_scraper.py
│   ├── processing/
│   │   ├── embedder.py
│   │   └── batch_processor.py
│   ├── retrieval/
│   │   ├── rag_pipeline.py
│   │   └── vector_store.py
│   ├── ui/app.py
│   └── utils/logger.py
└── tests/
```

## Operations and Maintenance

- **Reset database:**  
  ```bash
  dropdb xsearch
  dropuser xsearch_user
  ```  
  Then rerun `python3 main.py` (or `python src/database/migrate.py`) to recreate schema/data.

- **Rebuild embeddings:** delete `data/vector_store` and run `python src/processing/batch_processor.py --task embeddings`.

- **Change database targets:** pass `--db-name` / `--db-user` to `main.py` and keep `.env` synchronized with the same connection string.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `relation "tweets" does not exist` | Run `python src/database/migrate.py` to apply `schema/001_initial_schema.sql`. |
| Importer complains about missing `like.js` | Ensure the file lives at `inputs/twitter/data/like.js` or pass `--file` to the importer. |
| No results returned | Verify embeddings exist (`ls data/vector_store/tweets`) and rerun the embedding task if empty. |
| Streamlit cannot connect to DB | Check PostgreSQL service status (`pg_isready`) and confirm `.env` matches the actual database/user. |
| Handles show as `@i` | Re-import likes after ensuring network access so `import_likes.py` can follow `i/web` redirects. |

## License

MIT License. See `LICENSE` for details.
