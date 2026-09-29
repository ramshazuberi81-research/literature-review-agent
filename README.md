# Literature Review Agent

An AI agent that searches academic literature on a topic, extracts structured
data per paper, identifies concrete gaps in the field, and writes a literature
review with citations that are mechanically and semantically verified against
the source corpus — reducing the citation-hallucination problem common to
LLM-generated reviews.

## What it does

1. **Search** — queries Semantic Scholar, OpenAlex, and PubMed in parallel,
   dedupes results by DOI/title.
2. **Filter** — a batched LLM pass drops off-topic results before spending
   tokens on deep extraction.
3. **Extract** — one LLM call per surviving paper, forced into a fixed JSON
   schema (method, dataset, sample size, key finding, limitations, study
   type). This structured layer is what the rest of the pipeline is grounded
   in.
4. **Gap analysis** — checks the corpus against a taxonomy you define
   (e.g. population diversity, external validation, interpretability),
   producing specific gaps rather than generic "more research is needed."
5. **Synthesize** — writes the review thematically, citing only papers in the
   corpus by index.
6. **Verify (index-level)** — mechanically checks every citation index in the
   generated text actually exists in the corpus.
7. **Verify (claim-level)** — for every cited sentence, an LLM checks whether
   the cited paper's abstract + extracted fields actually support the claim,
   and flags supported / partial / unsupported.
8. **Author landscape** — ranks the most frequent authors in your corpus and
   checks which are still actively publishing, for outreach/context.

## Why the verification steps matter

Most "AI writes a lit review" demos stop at step 5, which means every
citation is only as trustworthy as the model's training data — a known
source of fabricated references. Steps 6–7 make that failure mode visible
and measurable instead of invisible.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...      # or adapt llm_client.py for your provider of choice
export S2_API_KEY=...             # optional, raises Semantic Scholar's rate limit
```

Edit `config.py`: set your `TOPIC` and `GAP_TAXONOMY`.

## Run

```bash
python main.py              # search -> extract -> gap analysis -> review
python verify_claims.py     # claim-level fact-check against the corpus
python author_landscape.py  # who's currently active in this space
```

## Known limitations

- Extraction is abstract-only — full-text extraction (e.g. via GROBID) would
  reduce false "unsupported" flags and catch more nuanced claims.
- Claim verification uses an LLM and is not perfect — treat "supported" as
  "probably fine," not "certainly correct." Spot-check regardless.
- Search coverage depends on Semantic Scholar / OpenAlex / PubMed indexing;
  field-specific databases may find papers this won't.
- This produces a strong first draft, not a submission-ready review. The
  framing, argument, and editorial judgment are still yours.

## License

MIT
