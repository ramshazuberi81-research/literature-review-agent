"""
Claim-level citation check, using YOUR existing Groq setup (llm_client.py).

Run from the lit_review folder:
    python verify_claims.py

Reads literature_review.md + extracted_cache.json, writes claim_verification.md.
Progress is saved to claim_verification_checkpoint.json after every batch, so if
the Groq daily quota runs out you can just rerun later and it resumes where it
stopped. Delete the checkpoint file to start from scratch.
"""
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher

from llm_client import invoke_with_retry
import llm_client

REVIEW_PATH = "literature_review.md"
CACHE_PATH = "extracted_cache.json"
REPORT_PATH = "claim_verification.md"
CHECKPOINT_PATH = "claim_verification_checkpoint.json"
BATCH_SIZE = 6


def get_llm():
    for name in ("get_llm", "build_llm", "make_llm", "llm"):
        obj = getattr(llm_client, name, None)
        if obj is None:
            continue
        if hasattr(obj, "invoke"):
            return obj
        if callable(obj):
            return obj()
    from langchain_groq import ChatGroq
    return ChatGroq(model="openai/gpt-oss-20b", temperature=0)


def load_papers(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("papers") or next((v for v in data.values() if isinstance(v, list)), [])
    return data


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def build_index_map(review, papers):
    """Map each [n] used in the review to the matching index in the cache, by reference title."""
    parts = re.split(r"\n#+\s*References[^\n]*\n", review, maxsplit=1)
    if len(parts) < 2:
        return {i: i for i in range(len(papers))}
    imap = {}
    titles = [_norm(p.get("title", "")) for p in papers]
    for line in parts[1].split("\n"):
        m = re.match(r"\s*\[(\d+)\]\s*(.+)", line) or re.match(r"\s*(\d+)\.\s+(.+)", line)
        if not m:
            continue
        n, text = int(m.group(1)), _norm(m.group(2))
        best, best_score = None, 0.0
        for j, t in enumerate(titles):
            if not t:
                continue
            score = 1.0 if t[:60] in text else SequenceMatcher(None, t, text).quick_ratio() * 0.6
            if score > best_score:
                best, best_score = j, score
        if best is not None and best_score >= 0.5:
            imap[n] = best
    return imap or {i: i for i in range(len(papers))}


def split_cited_sentences(text):
    text = re.split(r"\n#+\s*References", text, maxsplit=1)[0]
    out = []
    for line in text.split("\n"):
        if line.strip().startswith("#"):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", line):
            idxs = []
            for m in re.finditer(r"\[([\d,\s]+)\]", sent):
                idxs += [int(n) for n in m.group(1).split(",") if n.strip().isdigit()]
            if idxs:
                out.append((sent.strip(), sorted(set(idxs))))
    return out


def paper_block(n, p):
    e = p.get("extracted") or {}
    return (
        f"[{n}] {p.get('title','?')} ({p.get('year','?')})\n"
        f"Abstract: {str(p.get('abstract',''))[:1500]}\n"
        f"Extracted: {json.dumps(e)[:800]}"
    )


def parse_json_array(text):
    a, b = text.find("["), text.rfind("]")
    if a == -1 or b == -1:
        return None
    try:
        return json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return None


def verify_batch(llm, batch, papers, imap):
    # review number n -> paper via imap; skip numbers we can't resolve
    needed = sorted({n for _, idxs in batch for n in idxs
                     if imap.get(n) is not None and imap[n] < len(papers)})
    sources = "\n\n".join(paper_block(n, papers[imap[n]]) for n in needed)
    claims = "\n".join(f"C{k}: {s}  (cites {ix})" for k, (s, ix) in enumerate(batch))
    prompt = f"""You are a strict fact-checker for a literature review. For each claim, decide
whether the cited source paper(s) below support it. Use ONLY the source text provided.

SOURCES:
{sources}

CLAIMS:
{claims}

Verdicts: "supported" (clearly stated or directly implied), "partial" (part supported, part
overstated/generalized/missing), "unsupported" (the cited papers do not say this).

Return ONLY a JSON array, one object per claim, in order:
[{{"claim":"C0","verdict":"supported|partial|unsupported","reason":"<one short sentence>"}}]"""
    resp = invoke_with_retry(llm, prompt)
    text = getattr(resp, "content", resp)
    if isinstance(text, list):
        text = " ".join(t.get("text", "") if isinstance(t, dict) else str(t) for t in text)
    return parse_json_array(str(text))


def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_checkpoint(done):
    tmp = CHECKPOINT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(done, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CHECKPOINT_PATH)  # atomic, so a crash can't corrupt it


def write_report(sentences, done):
    results = []
    for sent, idxs in sentences:
        v = done.get(sent)
        if v:
            results.append({"sentence": sent, "cited": idxs, **v})
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    total = max(len(results), 1)

    lines = ["# Claim verification report\n",
             f"Claims checked: {len(results)} of {len(sentences)}\n"]
    for k, n in counts.items():
        lines.append(f"- {k}: {n} ({n/total:.0%})")
    lines.append("\n## Flagged claims (fix or remove)\n")
    for r in results:
        if r["verdict"] != "supported":
            lines.append(f"**[{r['verdict'].upper()}]** {r['sentence']}\n> {r['reason']}\n")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return counts


def main():
    with open(REVIEW_PATH, encoding="utf-8") as f:
        review = f.read()
    papers = load_papers(CACHE_PATH)
    imap = build_index_map(review, papers)
    sentences = split_cited_sentences(review)

    unresolved = sorted({n for _, idxs in sentences for n in idxs if n not in imap})
    if unresolved:
        print(f"Warning: citations with no matching paper: {unresolved}")

    done = load_checkpoint()
    pending = [(s, ix) for s, ix in sentences if s not in done]
    print(f"{len(sentences)} cited claims, {len(papers)} papers, "
          f"{len(done)} already verified, {len(pending)} to go")

    llm = get_llm()
    interrupted = False
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        print(f"  Verifying {start+1}-{start+len(batch)} of {len(pending)} pending...")
        try:
            verdicts = verify_batch(llm, batch, papers, imap) or []
        except RuntimeError as e:
            print(f"\nStopped: {e}")
            interrupted = True
            break
        except Exception as e:  # e.g. raw RateLimitError that slipped past retry
            print(f"\nStopped on unexpected error: {type(e).__name__}: {e}")
            interrupted = True
            break

        for k, (sent, _) in enumerate(batch):
            v = verdicts[k] if k < len(verdicts) and isinstance(verdicts[k], dict) else {}
            if v.get("verdict") in ("supported", "partial", "unsupported"):
                done[sent] = {"verdict": v["verdict"], "reason": v.get("reason", "")}
            # otherwise leave it out so the next run retries it
        save_checkpoint(done)
        time.sleep(1)

    counts = write_report(sentences, done)
    remaining = len([1 for s, _ in sentences if s not in done])
    print(f"\n{counts}\nReport: {REPORT_PATH}")
    if interrupted or remaining:
        print(f"{remaining} claims still unverified. Rerun later to resume "
              f"(progress is saved in {CHECKPOINT_PATH}).")
        sys.exit(1 if interrupted else 0)


if __name__ == "__main__":
    main()