"""
Step 2 & 3: filter candidates for relevance, then extract structured fields
per paper using the LLM.
"""

import json
import re

import config
from llm_client import get_llm, invoke_with_retry

FILTER_PROMPT = """You are screening papers for a literature review on the topic: "{topic}"

For each paper below, decide if it is relevant enough to include. Err toward
inclusion if the paper concerns EEG or brain-computer interfaces, cognitive load,
neurofeedback, memory encoding or consolidation, or adaptive instructional or
spaced-repetition systems, even if it doesn't cover every aspect of the topic.
Exclude papers that are clearly unrelated (e.g. purely clinical EEG for epilepsy
or sleep staging with no learning or memory angle).

Return ONLY a JSON list of 0-indexed integers for the papers to KEEP. No other text.

Papers:
{papers_block}
"""

EXTRACT_PROMPT = """Extract structured information from this paper abstract for a literature review on "{topic}".

Title: {title}
Year: {year}
Abstract: {abstract}

Return ONLY valid JSON with these exact keys:
{{
  "objective": "one sentence on what the paper set out to do",
  "method": "brief description of method/approach/model used",
  "dataset": "dataset(s) used, or 'not specified'",
  "sample_size": "number of participants/subjects, or 'not specified'",
  "key_findings": "1-2 sentence summary of main results",
  "limitations": "stated or apparent limitations",
  "relevance_to_topic": "one sentence on how this relates to the topic"
}}
"""


def _extract_json(text):
    """Pull the first JSON object or list out of a model response."""
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in model output: {text[:200]}")
    return json.loads(match.group(0))


def filter_relevant_papers(candidates, topic, batch_size=10):
    """Batch-screen candidates; fails open (keeps the batch) if a call errors."""
    llm = get_llm(temperature=0.0)
    keep_indices = set()

    for start in range(0, len(candidates), batch_size):
        batch = candidates[start:start + batch_size]
        papers_block = "\n".join(
            f"{i}. {p['title']} ({p.get('year') or 'n.d.'}) — "
            f"{(p.get('abstract') or '(no abstract, judge by title)')[:300]}"
            for i, p in enumerate(batch)
        )
        prompt = FILTER_PROMPT.format(topic=topic, papers_block=papers_block)
        try:
            response = invoke_with_retry(llm, prompt)
            local_indices = _extract_json(response.content)
            kept = [int(i) for i in local_indices if 0 <= int(i) < len(batch)]
            keep_indices.update(start + i for i in kept)
            print(f"    batch {start // batch_size + 1}: kept {len(kept)}/{len(batch)}")
        except Exception as e:
            print(f"  [warn] filter batch starting at {start} failed: {e}")
            keep_indices.update(range(start, start + len(batch)))  # fail open

    return [p for i, p in enumerate(candidates) if i in keep_indices]


def extract_all(papers):
    """Extract fields per paper. Papers whose extraction fails are dropped,
    not kept as empty placeholders."""
    llm = get_llm(temperature=0.0)
    extracted = []

    for i, p in enumerate(papers):
        print(f"  [{i+1}/{len(papers)}] {p['title'][:70]}")
        prompt = EXTRACT_PROMPT.format(
            topic=config.TOPIC,
            title=p["title"],
            year=p.get("year") or "n.d.",
            abstract=(p.get("abstract") or "")[:1200] or "(no abstract available)",
        )
        try:
            response = invoke_with_retry(llm, prompt)
            fields = _extract_json(response.content)
        except Exception as e:
            print(f"    [warn] extraction failed, skipping paper: {e}")
            continue
        extracted.append({**p, **fields})

    return extracted