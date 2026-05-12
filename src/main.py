from __future__ import annotations

import sys
from pathlib import Path

from .crawler import Crawler
from .indexer import Indexer
from .search import format_term_postings, urls_matching_phrase

DEFAULT_INDEX_PATH = Path("data/index.json")  # Default path in the data directory for the index file

# Handle user input
def _parse_line(line: str) -> tuple[str, list[str]]:
    parts = line.strip().split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]  # The first part is the command, the rest are arguments

# Run the interactive shell for the search engine
def run_shell(index_path: Path | None = None) -> None:
    path = index_path or DEFAULT_INDEX_PATH
    indexer: Indexer | None = None

    while True:
        try:
            line = input("> ")
        except EOFError:
            print()
            break

        cmd, rest = _parse_line(line)
        if not cmd:
            continue

        if cmd in ("quit", "exit", "q"):  # Exit the shell
            break

        if cmd == "help" or cmd == "?":  # Show help message
            print(
                "Commands: build [max_pages(optional)] | load | print <word> | "
                "find <words...> | quit"
            )
            continue

        if cmd == "build":
            max_pages: int | None = None
            if rest:
                try:
                    max_pages = int(rest[0])
                except ValueError:
                    print("Usage: build [max_pages] — max_pages must be an integer.")
                    continue
                if max_pages < 1:
                    print("max_pages must be at least 1.")
                    continue
                print(f"Crawling and indexing (at most {max_pages} page(s))...")
            else:
                print(
                    "Crawling and indexing..."
                )
            idx = Indexer()
            pages = idx.crawl_and_index(Crawler(), max_pages=max_pages)
            path.parent.mkdir(parents=True, exist_ok=True)
            idx.save(path)
            indexer = idx
            print(f"Indexed {pages} page(s); index saved to {path.resolve()}")
            continue

        if cmd == "load":
            try:
                indexer = Indexer.load(path)  # Load the index from the json file
            except FileNotFoundError:
                print(f"No index file at {path.resolve()}.")
                continue
            except (OSError, ValueError) as exc:
                print(f"Failed to load index: {exc}")
                continue
            print(f"Loaded index from {path.resolve()}")
            continue

        if cmd == "print":
            if not rest:  # If no word is provided
                print("Usage: print <word>")
                continue
            if indexer is None:  # If index is not loaded
                print("No index in memory. Run 'build' or 'load' first.")
                continue
            word = rest[0]  # The first word is considered for printing
            print(format_term_postings(word, indexer.lookup(word)))
            continue

        if cmd == "find":
            if not rest:
                print("Usage: find <query words...>")
                continue
            if indexer is None:
                print("No index in memory. Run 'build' or 'load' first.")
                continue
            phrase = " ".join(rest)  # Join the rest of the words to form the query phrase
            urls = urls_matching_phrase(indexer, phrase)
            if not urls:
                print("(no matching pages)")
            else:
                for u in urls:
                    print(u)
            continue

        print(f"Unknown command: {cmd!r}. Type 'help' for a list of commands.")  # Handle unknown commands

# Main entry point for the script
def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    index_path = Path(argv[0]).resolve() if argv else DEFAULT_INDEX_PATH
    run_shell(index_path)


if __name__ == "__main__":
    main()
