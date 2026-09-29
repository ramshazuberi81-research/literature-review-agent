"""
Step 4: identify gaps in the literature using a fixed taxonomy of gap types.

- Row 0 (small cohorts) is computed in code from each paper's sample_size field.
- Every other row comes from batched LLM calls that ask a POSITIVE question per
  paper ("does this paper explicitly do X?"). A gap is reported as present only
  when few or no papers do X. Aggregation happens in code, not in the model.
"""

import json
import re
import time

from llm_client import get_llm, invoke_with_retry

REVIEW_HINTS = (
    "review", "update", "consensus", "perspective", "overview",
    "meta-analysis", "guidelines", "what is", "primer", "tutorial",
)

SMALL_N_PREFIX = "small subject cohorts"
SMALL_N_THRESHOLD = 15

CHUNK_SIZE = 8   # papers per LLM call
PAUSE_S = 20     # ~2-3k tokens per call; keeps you under an 8k TPM limit

# Aligned with gap_taxonomy[1:]: what a paper must DO to count against the gap.
CHECKS = [
    "tested in a real classroom or naturalistic setting (not a lab)",
    "used EEG to change what or when material is presented, in closed loop",
    "used consumer-grade dry EEG (e.g. Muse, Emotiv Insight, NeuroSky)",
    "analysed or accounted for individual differences in theta/alpha response",
    "measured retention after a delay or across multiple sessions",
    "controlled or reported confounds (fatigue, caffeine, mood, time of day)",
    "compared against a fixed-interval or non-adaptive baseline",
    "learned a scheduling policy from delayed recall feedback (bandit / RL)",
]

CHUNK_PROMPT = """Studies for a literature review on "{topic}".
For each check, list the numbers of studies whose line EXPLICITLY states it.
If a line doesn't say so, don't list it. Never guess.

Checks:
{checks}

Studies:
{corpus}

Reply with JSON only, no other text, e.g. {{"c1": [3], "c2": [], ...}} covering c1..c{n}."""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _is_empirical(p):
    study_type = str(p.get("study_type", "")).lower()
    if study_type:
        return "review" not in study_type and "perspective" not in study_type
    title = (p.get("title") or "").lower()
    return not any(h in title for h in REVIEW_HINTS)


def _short(value, n=160):
    value = str(value or "not stated")
    return value if len(value) <= n else value[:n] + "..."


def _parse_hits(text, n_checks):
    """Extract {"c1": [...], ...} from model output; tolerant of code fences."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError(f"no JSON in output (len={len(text or '')})")
    data = json.loads(m.group(0))
    out = {}
    for k in range(1, n_checks + 1):
        vals = data.get(f"c{k}") or []
        out[k] = [int(x) for x in vals if str(x).isdigit()]
    return out


def sample_size_row(extracted, category, threshold=SMALL_N_THRESHOLD):
    """Deterministic sample-size gap row, computed from the sample_size field.
    Takes the largest number in the field, so '17 older adults (12 females)'
    reads as 17 and '2 groups of 20' is not misread as 2."""
    small, known, unknown = [], [], []
    for i, p in enumerate(extracted, start=1):
        if not _is_empirical(p):
            continue
        raw = str(p.get("sample_size") or "")
        numbers = [int(n) for n in re.findall(r"\d+", raw)]
        if not numbers or "not specified" in raw.lower():
            unknown.append(i)
            continue
        n = max(numbers)
        known.append(i)
        if n < threshold:
            small.append((i, n))

    total = len(known) + len(unknown)
    parts = [f"n is stated for only {len(known)} of {total} empirical papers."]
    if small:
        parts.append(
            f"Under {threshold}: "
            + ", ".join(f"paper {i} (n={n})" for i, n in small) + "."
        )
    if unknown:
        parts.append(f"Not stated in the abstract for papers {', '.join(map(str, unknown))}.")
    return {
        "category": category,
        "present": bool(small),
        "evidence": " ".join(parts),
        "severity": "medium" if len(small) >= 2 else "low",
    }


def _override_sample_row(gaps, extracted, gap_taxonomy):
    """Replace (or insert) the sample-size row with the computed one."""
    category = next(
        (g for g in gap_taxonomy if g.lower().startswith(SMALL_N_PREFIX)), None
    )
    if not category:
        return gaps
    row = sample_size_row(extracted, category)
    for idx, g in enumerate(gaps):
        if str(g.get("category", "")).lower().startswith(SMALL_N_PREFIX):
            gaps[idx] = row
            return gaps
    gaps.append(row)
    return gaps


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def run_gap_analysis(extracted, topic, gap_taxonomy):
    if not extracted:
        return [
            {"category": g, "present": False,
             "evidence": "No papers in corpus to analyze.", "severity": "n/a"}
            for g in gap_taxonomy
        ]

    # Keep ORIGINAL numbering so gap citations match the review's citations.
    numbered = list(enumerate(extracted, start=1))
    empirical = [(i, p) for i, p in numbered if _is_empirical(p)] or numbered
    print(f"  (gap analysis using {len(empirical)}/{len(extracted)} empirical papers)")

    assert len(CHECKS) == len(gap_taxonomy) - 1, "CHECKS must align with taxonomy[1:]"
    llm = get_llm(temperature=0.1)
    valid = {i for i, _ in empirical}
    checks_block = "\n".join(f"c{k}: {c}" for k, c in enumerate(CHECKS, 1))
    hits = {k: set() for k in range(1, len(CHECKS) + 1)}
    failed = 0

    for start in range(0, len(empirical), CHUNK_SIZE):
        chunk = empirical[start:start + CHUNK_SIZE]
        corpus_block = "\n".join(
            f"[{i}] {_short(p.get('title'), 80)} | "
            f"method: {_short(p.get('method'), 100)} | "
            f"findings: {_short(p.get('key_findings'), 100)} | "
            f"limitations: {_short(p.get('limitations'), 100)}"
            for i, p in chunk
        )
        prompt = CHUNK_PROMPT.format(
            topic=topic, checks=checks_block,
            corpus=corpus_block, n=len(CHECKS),
        )

        ok = False
        for attempt in range(2):
            resp = None
            try:
                resp = invoke_with_retry(llm, prompt)
                for k, nums in _parse_hits(resp.content, len(CHECKS)).items():
                    hits[k].update(n for n in nums if n in valid)
                ok = True
                break
            except Exception as e:
                reason = ""
                meta = getattr(resp, "response_metadata", None) or {}
                if meta.get("finish_reason"):
                    reason = f" (finish_reason={meta['finish_reason']})"
                print(f"  [warn] batch at paper {chunk[0][0]}, "
                      f"attempt {attempt + 1}: {e}{reason}")
        if not ok:
            failed += 1
        time.sleep(PAUSE_S)

    rows = [{"category": gap_taxonomy[0]}]  # placeholder, replaced by computed row
    for k, cat in enumerate(gap_taxonomy[1:], 1):
        papers = sorted(hits[k])
        listed = ", ".join(map(str, papers))
        if not papers and failed:
            row = (None, f"{failed} batch(es) failed; not assessed.", "unknown")
        elif not papers:
            row = (True, "No paper's abstract-level summary states this.", "high")
        elif len(papers) < 3:
            row = (True, f"Only papers {listed} state this.", "medium")
        else:
            row = (False, f"Papers {listed} state this.", "low")
        rows.append({"category": cat, "present": row[0],
                     "evidence": row[1], "severity": row[2]})
    return _override_sample_row(rows, extracted, gap_taxonomy)