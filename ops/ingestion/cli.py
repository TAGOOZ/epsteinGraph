#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from crawler import crawl_listing_pages
from downloader import download_all
from process import process_pdf
from state import load_state, save_state


def cmd_crawl(args: argparse.Namespace) -> None:
    seeds = read_seeds_file(Path(args.seeds))
    urls = crawl_listing_pages(
        seeds=seeds,
        allowed_hosts=set(args.allowed_host),
        blocked_path_substrings=set(args.blocked_path_substring),
        allowed_extensions=set(args.allowed_ext),
        rate_limit_seconds=args.rate_limit_seconds,
        user_agent=args.user_agent,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sorted(urls), indent=2), encoding="utf-8")
    print(f"Wrote {len(urls)} URLs to {output_path}")


def cmd_download(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    urls = json.loads(input_path.read_text(encoding="utf-8"))

    state_path = Path(args.state)
    state = load_state(state_path)

    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    updated_state = download_all(
        urls=urls,
        state=state,
        download_dir=download_dir,
        rate_limit_seconds=args.rate_limit_seconds,
        user_agent=args.user_agent,
    )

    save_state(state_path, updated_state)
    print(f"Updated state at {state_path}")


def cmd_process(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    urls = json.loads(input_path.read_text(encoding="utf-8"))
    state_path = Path(args.state)
    state = load_state(state_path)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    for url in urls:
        meta = state.get("url_meta", {}).get(url)
        if not meta:
            continue
        file_path = Path(meta["path"])
        if not file_path.exists():
            continue
        if not is_pdf_file(file_path):
            meta["process_skip"] = "non_pdf"
            skipped += 1
            continue
        try:
            result = process_pdf(file_path, output_dir)
        except Exception as exc:  # pragma: no cover - runtime safety
            meta["process_error"] = str(exc)
            skipped += 1
            continue
        meta["processed_output"] = result["output"]
        meta["chunk_count"] = result["chunks"]
        processed += 1

    save_state(state_path, state)
    print(f"Processed {processed} files (skipped {skipped})")


def is_pdf_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            header = handle.read(5)
    except OSError:
        return False
    return header.startswith(b"%PDF")


def cmd_load_db(args: argparse.Namespace) -> None:
    database_url = args.database_url or ""
    if not database_url:
        database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required (or pass --database-url)")

    from db_writer import load_processed_into_db

    state_path = Path(args.state)
    inserted = load_processed_into_db(
        database_url=database_url,
        state_path=state_path,
        max_docs=args.max_docs,
    )
    print(f"Loaded {inserted} documents into Postgres")


def cmd_index(args: argparse.Namespace) -> None:
    meili_host = args.meili_host or os.environ.get("MEILI_HOST", "")
    meili_key = args.meili_master_key or os.environ.get("MEILI_MASTER_KEY", "")
    if not meili_host or not meili_key:
        raise SystemExit("MEILI_HOST and MEILI_MASTER_KEY are required")

    from indexer import MeiliIndexer, build_chunk_records, load_processed_outputs

    state_path = Path(args.state)
    state = load_state(state_path)
    indexer = MeiliIndexer(meili_host, meili_key)

    batch: list[dict] = []
    total = 0
    for url, payload in load_processed_outputs(state_path=state_path, max_docs=args.max_docs):
        meta = state.get("url_meta", {}).get(url, {})
        chunks = build_chunk_records(url=url, meta=meta, payload=payload)
        batch.extend(chunks)
        total += len(chunks)

        if len(batch) >= args.batch_size:
            indexer.upsert_chunks(batch)
            batch = []

    if batch:
        indexer.upsert_chunks(batch)

    print(f"Indexed {total} chunks into Meilisearch")


def read_seeds_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    seeds = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        seeds.append(line)
    return seeds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DOJ dataset ingestion tools (crawl + download)"
    )
    parser.add_argument(
        "--user-agent",
        default="epsteinGraph/0.1 (contact: TBD)",
        help="HTTP User-Agent string",
    )
    parser.add_argument(
        "--rate-limit-seconds",
        type=float,
        default=1.0,
        help="Minimum delay between HTTP requests",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    crawl = sub.add_parser("crawl", help="Crawl listing pages for file URLs")
    crawl.add_argument(
        "--seeds",
        default=str(Path("ops/ingestion/seeds.example.txt")),
        help="Path to seeds file",
    )
    crawl.add_argument(
        "--output",
        default=str(Path("ops/ingestion/state/urls.json")),
        help="Output JSON path for URLs",
    )
    crawl.add_argument(
        "--allowed-host",
        action="append",
        default=["www.justice.gov", "justice.gov"],
        help="Allowed host (repeatable)",
    )
    crawl.add_argument(
        "--blocked-path-substring",
        action="append",
        default=["/epstein/search"],
        help="Blocked path substring (repeatable)",
    )
    crawl.add_argument(
        "--allowed-ext",
        action="append",
        default=[".pdf", ".zip"],
        help="Allowed file extension (repeatable)",
    )
    crawl.set_defaults(func=cmd_crawl)

    download = sub.add_parser("download", help="Download and hash files")
    download.add_argument(
        "--input",
        default=str(Path("ops/ingestion/state/urls.json")),
        help="Input JSON path for URLs",
    )
    download.add_argument(
        "--state",
        default=str(Path("ops/ingestion/state/state.json")),
        help="State JSON path",
    )
    download.add_argument(
        "--download-dir",
        default=str(Path("ops/ingestion/state/downloads")),
        help="Directory to store downloaded files",
    )
    download.set_defaults(func=cmd_download)

    process = sub.add_parser(
        "process", help="Extract text and chunk PDFs into JSON outputs"
    )
    process.add_argument(
        "--input",
        default=str(Path("ops/ingestion/state/urls.json")),
        help="Input JSON path for URLs",
    )
    process.add_argument(
        "--state",
        default=str(Path("ops/ingestion/state/state.json")),
        help="State JSON path",
    )
    process.add_argument(
        "--output-dir",
        default=str(Path("ops/ingestion/state/processed")),
        help="Directory to store processed JSON outputs",
    )
    process.set_defaults(func=cmd_process)

    load_db = sub.add_parser(
        "load-db", help="Load processed outputs into Postgres (documents + chunks)"
    )
    load_db.add_argument(
        "--state",
        default=str(Path("ops/ingestion/state/state.json")),
        help="State JSON path",
    )
    load_db.add_argument(
        "--database-url",
        default="",
        help="Postgres connection string (defaults to DATABASE_URL env var)",
    )
    load_db.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Optional limit on number of documents to load",
    )
    load_db.set_defaults(func=cmd_load_db)

    index = sub.add_parser(
        "index", help="Index processed chunks into Meilisearch"
    )
    index.add_argument(
        "--state",
        default=str(Path("ops/ingestion/state/state.json")),
        help="State JSON path",
    )
    index.add_argument(
        "--meili-host",
        default="",
        help="Meilisearch host (defaults to MEILI_HOST env var)",
    )
    index.add_argument(
        "--meili-master-key",
        default="",
        help="Meilisearch master key (defaults to MEILI_MASTER_KEY env var)",
    )
    index.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Optional limit on number of documents to index",
    )
    index.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Chunk batch size for indexing",
    )
    index.set_defaults(func=cmd_index)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
