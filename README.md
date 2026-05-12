# Web Search Engine Tool

## Project overview and purpose

This is a search engine for the **Web Services and Web Data** module. It combines a small HTTP crawler, an inverted index over page text, and an interactive shell so you can build or load an index, inspect term postings, and run conjunctive phrase-style queries (case-insensitive).

The default crawl target is [quotes.toscrape.com](https://quotes.toscrape.com/), with a **6 second politeness delay** between HTTP requests. The index is stored as JSON (by default under `data/index.json`).

---

## Dependencies and how to install them

| Package        | Role                                      |
|----------------|-------------------------------------------|
| **requests**   | HTTP client used by the crawler          |
| **beautifulsoup4** | HTML parsing and visible text extraction |
| **pytest**     | Test runner (used for the test suite)    |

Install everything listed in `requirements.txt` from the project root:

```bash
pip install -r requirements.txt
```

Use **Python 3.10+**.

---

## Installation and setup

1. Clone or copy this repository onto your machine.
2. Create and activate a virtual environment:
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the interactive shell from the **project root** (the folder that contains `src/` and `data/`):

   ```bash
   python -m src.main
   ```

   Optional: pass a custom index file path (resolved to an absolute path):

   ```bash
   python -m src.main path/to/my_index.json
   ```

   If you omit the argument, the default index path is `data/index.json`.

5. In the shell, type `help` or `?` for a short command summary. Use `quit`, `exit`, or `q` to leave.

---

## Usage examples

You must run **`build`** or **`load`** before **`print`** or **`find`**, so that an index is in memory.

### 1. `build` — crawl and build the index

Crawl the configured site, build the inverted index, and save it to the index file (default: `data/index.json`).

```text
> build
```

Limit how many pages are fetched (must be a positive integer):

```text
> build 5
```

### 2. `load` — load an existing index from disk

Load a previously saved JSON index without crawling:

```text
> load
```

### 3. `print` — show postings for one term

Show how one word appears across indexed URLs (frequencies and positions). The lookup is case-insensitive.

```text
> print love
```

### 4. `find` — search for pages containing all query words

Provide one or more words; URLs are listed where all token appears somewhere in the page text.

```text
> find change deep
```

Single-word query:

```text
> find quotes
```

---

## Testing instructions

From the **project root**, run quietly with a summary:

```bash
python -m pytest -q
```

Run a single file:

```bash
python -m pytest tests/test_crawler.py
```

```bash
python -m pytest tests/test_indexer.py
```

```bash
python -m pytest tests/test_search.py
```

The suite covers URL normalisation and crawling behaviour, indexing and save/load, and search/formatting helpers. Crawler tests use mocks where appropriate.
