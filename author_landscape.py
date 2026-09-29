"""
Author landscape analysis.

Ranks the authors present in an extracted paper corpus by frequency of
appearance, then queries Semantic Scholar to determine which are still
actively publishing and their current affiliation. Useful for identifying
key researchers and potential collaborators/reviewers for a given topic
after running the extraction pipeline (see extract.py).

Uses the public Semantic Scholar Graph API (no key required). Setting an
S2_API_KEY environment variable raises the default rate limit.

Progress is checkpointed after every lookup, so an interrupted run (e.g.
from rate limiting) can be resumed by rerunning the script. Delete the
checkpoint file to start over.

Usage:
    python author_landscape.py

Reads:  extracted_cache.json
Writes: current_landscape.md
"""
import json
import os
import time
import requests

CACHE_PATH = "extracted_cache.json"
OUTPUT_PATH = "current_landscape.md"
CHECKPOINT_PATH = "current_landscape_checkpoint.json"
TOP_N_AUTHORS = 12
RECENT_YEARS = 2
CURRENT_YEAR = 2026
SLEEP_BETWEEN = 3.0
MAX_RETRIES = 5

S2_API_KEY = os.environ.get("S2_API_KEY")


def load_papers(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("papers") or next((v for v in data.values() if isinstance(v, list)), [])
    return data


def rank_authors(papers, top_n=TOP_N_AUTHORS):
    """Return the most frequently appearing authors across the corpus."""
    counts = {}
    for paper in papers:
        for author in paper.get("authors", []):
            counts[author] = counts.get(author, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n]


def lookup_author(name):
    """
    Query the Semantic Scholar author-search endpoint for a given name.
    Retries with exponential backoff on HTTP 429 (rate limited).
    Returns a dict of author info, or None if no match is found.
    """
    url = "https://api.semanticscholar.org/graph/v1/author/search"
    params = {
        "query": name,
        "fields": "name,affiliations,hIndex,paperCount,papers.year,papers.title",
    }
    headers = {"x-api-key": S2_API_KEY} if S2_API_KEY else {}

    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 429:
            wait = min(2 ** attempt, 60)
            print(f"    Rate limited, waiting {wait}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
            continue

        response.raise_for_status()
        results = response.json().get("data", [])
        if not results:
            return None

        match = results[0]
        recent_papers = [
            p for p in match.get("papers", [])
            if p.get("year") and p["year"] >= CURRENT_YEAR - RECENT_YEARS
        ]
        return {
            "name": match.get("name"),
            "affiliations": match.get("affiliations") or [],
            "h_index": match.get("hIndex"),
            "paper_count": match.get("paperCount"),
            "recent_papers": sorted(
                recent_papers, key=lambda p: p.get("year", 0), reverse=True
            )[:3],
        }

    raise RuntimeError(f"Rate limited after {MAX_RETRIES} attempts looking up '{name}'")


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_PATH):
        return {}
    try:
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_checkpoint(results):
    tmp_path = CHECKPOINT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    os.replace(tmp_path, CHECKPOINT_PATH)  # atomic write


def write_report(ranked_authors, results, corpus_size):
    lines = [
        "# Current Research Landscape\n",
        f"Authors ranked by frequency across a {corpus_size}-paper corpus, "
        f"cross-referenced with Semantic Scholar for recent activity.\n",
    ]
    for name, count in ranked_authors:
        info = results.get(name)
        lines.append(f"\n## {name} ({count} paper{'s' if count != 1 else ''} in corpus)")

        if info is None:
            lines.append("- Not yet checked.")
            continue
        if info == "not_found":
            lines.append("- No match found on Semantic Scholar.")
            continue

        if info.get("affiliations"):
            lines.append(f"- Affiliation: {', '.join(info['affiliations'])}")
        lines.append(
            f"- h-index: {info.get('h_index')}, "
            f"papers indexed: {info.get('paper_count')}"
        )
        if info.get("recent_papers"):
            lines.append(f"- Active in the last {RECENT_YEARS} years:")
            for paper in info["recent_papers"]:
                lines.append(f"  - {paper.get('title', 'Untitled')} ({paper.get('year', 'n.d.')})")
        else:
            lines.append(f"- No publications found in the last {RECENT_YEARS} years.")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    papers = load_papers(CACHE_PATH)
    ranked_authors = rank_authors(papers)

    results = load_checkpoint()
    pending = [(name, count) for name, count in ranked_authors if name not in results]

    print(f"{len(ranked_authors)} authors ranked, "
          f"{len(results)} already checked, {len(pending)} remaining")
    if not S2_API_KEY:
        print("No S2_API_KEY set; using unauthenticated requests (lower rate limit).")

    for name, _ in pending:
        print(f"Looking up {name}...")
        try:
            info = lookup_author(name)
            results[name] = info if info is not None else "not_found"
        except RuntimeError as e:
            print(f"\nStopped: {e}")
            print("Progress saved. Rerun the script to resume.")
            save_checkpoint(results)
            write_report(ranked_authors, results, len(papers))
            return
        save_checkpoint(results)
        time.sleep(SLEEP_BETWEEN)

    write_report(ranked_authors, results, len(papers))
    print(f"\nDone. Report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()