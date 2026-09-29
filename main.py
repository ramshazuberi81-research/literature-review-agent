"""
Orchestrator — runs the full pipeline end to end.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install -r requirements.txt
    python main.py

Edit TOPIC and GAP_TAXONOMY in config.py first.
"""

import json
import config
from search import gather_candidate_papers
from extract import filter_relevant_papers, extract_all
from gap_analysis import run_gap_analysis
from synthesize import write_literature_review, verify_citations
from verify_claims import verify_claims, write_report


def build_queries(topic):
    """
    Step 1a: expand one topic into several search phrasings.
    You can do this with an LLM call too — kept simple/manual here
    so the pipeline runs without burning tokens on query expansion.
    Edit this list to add synonyms/related terms for your field.
    """
    return [
        topic,
        f"{topic} machine learning",
        f"{topic} deep learning",
        f"{topic} systematic review",
        f"{topic} clinical validation",
    ]


def main():
    if not config.ANTHROPIC_API_KEY:
        raise SystemExit("Set ANTHROPIC_API_KEY environment variable first.")

    print(f"Topic: {config.TOPIC}\n")

    # Step 1: Search
    print("[1/7] Searching Semantic Scholar + OpenAlex + PubMed...")
    queries = build_queries(config.TOPIC)
    candidates = gather_candidate_papers(queries)
    print(f"  -> {len(candidates)} unique candidates found\n")

    # Step 2: Filter for relevance
    print("[2/7] Filtering for relevance...")
    relevant = filter_relevant_papers(candidates, config.TOPIC)
    print(f"  -> {len(relevant)} papers kept\n")

    # Step 3: Structured extraction
    print("[3/7] Extracting structured fields per paper...")
    extracted = extract_all(relevant)
    print()

    # Step 4: Gap analysis
    print("[4/7] Running gap analysis...")
    gaps = run_gap_analysis(extracted, config.TOPIC, config.GAP_TAXONOMY)
    print("  -> done\n")

    # Step 5: Synthesis
    print("[5/7] Writing literature review...")
    review_text, references = write_literature_review(extracted, gaps, config.TOPIC)
    print("  -> done\n")

    # Step 6: Verification
    print("[6/7] Verifying citation indices...")
    check = verify_citations(review_text, extracted)
    print(f"  -> {json.dumps(check, indent=2)}\n")

    # Step 7: Claim-level verification
    print("[7/7] Verifying each cited claim against its source paper...")
    claim_results, claim_counts = verify_claims(review_text, extracted)
    report_path = write_report(claim_results, claim_counts)
    print(f"  -> {claim_counts}  (details: {report_path})\n")

    # Write output
    with open(config.OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Literature Review: {config.TOPIC}\n\n")
        f.write(review_text)
        f.write("\n\n## References\n\n")
        f.write(references)
        f.write("\n\n---\n*Citation check:*\n```json\n")
        f.write(json.dumps(check, indent=2))
        f.write("\n```\n")
        f.write(f"\n*Claim check:* {json.dumps(claim_counts)} — see claim_verification.md\n")

    with open("gap_analysis.json", "w", encoding="utf-8") as f:
        json.dump(gaps, f, indent=2)

    print(f"Done. Review written to {config.OUTPUT_MD}")
    if not check["all_citations_valid"]:
        print(f"⚠️  WARNING: invalid citation indices found: {check['invalid_citation_indices']}")
        print("   Review these manually before trusting the output.")
    if check["papers_never_cited"]:
        print(f"ℹ️  {len(check['papers_never_cited'])} extracted papers were never cited — "
              f"consider whether they belong in the corpus.")
    imap = build_index_map(review, papers)
        verdicts = verify_batch(llm, batch, papers, imap) or []

    print(f"Mapped {len(imap)} references to cached papers; first 3: {list(imap.items())[:3]}")


if __name__ == "__main__":
    main()