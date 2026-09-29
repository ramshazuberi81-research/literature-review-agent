"""
Step 1: Search & fetch candidate papers
-----------------------------------------
Pulls from Semantic Scholar (best citation graph + abstracts) and
OpenAlex (broad coverage, good for non-CS fields). Dedupes by DOI/title.

Run standalone to sanity-check search results before running the
full pipeline:
    python search.py
"""

import re
import requests
import time
from difflib import SequenceMatcher
import config


def search_semantic_scholar(query, limit=40):
    """Semantic Scholar Graph API — free, no key required (key raises rate limit)."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,authors,venue,externalIds,citationCount,openAccessPdf",
    }
    headers = {}
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY

    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", [])

    papers = []
    for p in data:
        if not p.get("abstract"):
            continue
        if p.get("year") and p["year"] < config.MIN_YEAR:
            continue
        papers.append({
            "title": p.get("title", ""),
            "abstract": p.get("abstract", ""),
            "year": p.get("year"),
            "authors": [a["name"] for a in p.get("authors", [])],
            "venue": p.get("venue", ""),
            "doi": (p.get("externalIds") or {}).get("DOI"),
            "citation_count": p.get("citationCount", 0),
            "pdf_url": (p.get("openAccessPdf") or {}).get("url"),
            "source": "semantic_scholar",
        })
    return papers


def search_openalex(query, limit=40):
    """OpenAlex — free, no key required. Good fallback / cross-check."""
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per-page": min(limit, 50),
        "filter": f"from_publication_date:{config.MIN_YEAR}-01-01",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("results", [])

    papers = []
    for p in data:
        abstract = _reconstruct_openalex_abstract(p.get("abstract_inverted_index"))
        if not abstract:
            continue
        papers.append({
            "title": p.get("title", ""),
            "abstract": abstract,
            "year": p.get("publication_year"),
            "authors": [a["author"]["display_name"] for a in p.get("authorships", [])],
            "venue": (p.get("primary_location") or {}).get("source", {}).get("display_name", ""),
            "doi": p.get("doi", "").replace("https://doi.org/", "") if p.get("doi") else None,
            "citation_count": p.get("cited_by_count", 0),
            "pdf_url": (p.get("open_access") or {}).get("oa_url"),
            "source": "openalex",
        })
    return papers


def search_pubmed(query, limit=30):
    """PubMed via NCBI E-utilities. Free; set NCBI_API_KEY env var to raise rate limit."""
    import os
    import xml.etree.ElementTree as ET
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    key = os.environ.get("NCBI_API_KEY")
    common = {"api_key": key} if key else {}

    r = requests.get(f"{base}/esearch.fcgi", params={
        **common, "db": "pubmed", "term": query, "retmax": limit,
        "retmode": "json", "datetype": "pdat", "mindate": str(config.MIN_YEAR),
        "maxdate": "3000", "sort": "relevance",
    }, timeout=20)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    time.sleep(0.4)
    r = requests.get(f"{base}/efetch.fcgi", params={
        **common, "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
    }, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    papers = []
    for art in root.findall(".//PubmedArticle"):
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        abs_parts = ["".join(a.itertext()) for a in art.findall(".//Abstract/AbstractText")]
        abstract = " ".join(abs_parts).strip()
        if not abstract:
            continue
        year_el = art.find(".//JournalIssue/PubDate/Year")
        if year_el is None:
            medline = art.find(".//JournalIssue/PubDate/MedlineDate")
            m = re.search(r"\d{4}", medline.text) if medline is not None and medline.text else None
            year = int(m.group()) if m else None
        else:
            year = int(year_el.text)
        authors = []
        for a in art.findall(".//AuthorList/Author"):
            ln, fn = a.findtext("LastName"), a.findtext("ForeName")
            if ln:
                authors.append(f"{fn} {ln}".strip() if fn else ln)
        doi = None
        for aid in art.findall(".//ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text
        papers.append({
            "title": title, "abstract": abstract, "year": year, "authors": authors,
            "venue": art.findtext(".//Journal/Title") or "",
            "doi": doi, "citation_count": 0, "pdf_url": None, "source": "pubmed",
        })
    return papers


def _reconstruct_openalex_abstract(inverted_index):
    """OpenAlex stores abstracts as {word: [positions]} to save space."""
    if not inverted_index:
        return None
    position_map = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            position_map[pos] = word
    return " ".join(position_map[i] for i in sorted(position_map))


def _title_similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def dedupe(papers):
    """Dedupe by DOI first, then fuzzy title match."""
    seen_dois = set()
    unique = []
    for p in papers:
        if p["doi"] and p["doi"] in seen_dois:
            continue
        is_dupe = False
        for existing in unique:
            if _title_similarity(p["title"], existing["title"]) > 0.9:
                is_dupe = True
                break
        if not is_dupe:
            if p["doi"]:
                seen_dois.add(p["doi"])
            unique.append(p)
    return unique


def gather_candidate_papers(query_list):
    """
    Step 1 entry point: run multiple search queries across both APIs,
    merge and dedupe. query_list should be several phrasings of the
    topic (see build_queries in main.py).
    """
    all_papers = []
    for q in query_list:
        try:
            all_papers.extend(search_semantic_scholar(q, limit=25))
        except Exception as e:
            print(f"  [warn] Semantic Scholar failed for '{q}': {e}")
        time.sleep(1)  # be polite to the free tier

        try:
            all_papers.extend(search_openalex(q, limit=25))
        except Exception as e:
            print(f"  [warn] OpenAlex failed for '{q}': {e}")
        time.sleep(0.5)

        try:
            all_papers.extend(search_pubmed(q, limit=25))
        except Exception as e:
            print(f"  [warn] PubMed failed for '{q}': {e}")
        time.sleep(0.5)

    unique = dedupe(all_papers)
    # Round-robin across sources so PubMed (no citation counts) isn't buried
    by_src = {}
    for p in unique:
        by_src.setdefault(p["source"], []).append(p)
    for lst in by_src.values():
        lst.sort(key=lambda p: p.get("citation_count", 0), reverse=True)
    merged = []
    while any(by_src.values()) and len(merged) < config.MAX_PAPERS_TO_FETCH:
        for lst in by_src.values():
            if lst:
                merged.append(lst.pop(0))
    return merged[:config.MAX_PAPERS_TO_FETCH]


if __name__ == "__main__":
    results = gather_candidate_papers([config.TOPIC])
    print(f"Found {len(results)} unique papers")
    for p in results[:5]:
        print(f"- {p['title']} ({p['year']}) [{p['citation_count']} citations]")