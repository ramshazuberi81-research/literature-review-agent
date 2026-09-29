"""
Step 5 & 6: write the literature review with numbered citations, render the
Research Gaps section deterministically from the gap analysis, then verify
every citation marker (including grouped ones like [3, 7] and ranges [3-5]).

The review is written ONE SECTION PER LLM CALL. Each call sees only the papers
routed to that section (by keyword, in code), so prompts stay small enough for
low token-per-minute limits, and one failed section cannot wipe out the rest.
"""

import re
import time

from llm_client import get_llm, invoke_with_retry

PAUSE_S = 15          # pause between section calls (keeps under a small TPM limit)
MAX_PAPERS_PER_CALL = 8

# (heading, keywords matched against the paper title, description for the prompt)
# Routing checks themes in ROUTING_ORDER; a paper goes to the first theme that matches.
SECTIONS = {
    "foundations": (
        "Conceptual Foundations of Passive Brain-Computer Interfaces",
        (),
        "what passive BCIs are and how they have been framed and applied",
    ),
    "load": (
        "Cognitive Load and EEG-Based Workload Estimation",
        ("cognitive load", "workload", "working memory", "cognitive architecture",
         "instructional", "brain load", "cognitive workload"),
        "cognitive load theory and how EEG measures of load/workload are estimated",
    ),
    "decoding": (
        "Machine-Learning Decoding of EEG",
        ("deep learning", "convolutional", "classification", "neural network",
         "eegnet", "decoding", "algorithms", "motor-imagery", "motor imagery"),
        "algorithms and models used to decode EEG signals",
    ),
    "neurofeedback": (
        "Neurofeedback and Memory",
        ("neurofeedback",),
        "neurofeedback training and its effects on memory and cognition",
    ),
    "applications": (
        "Adaptive and Applied Systems",
        ("adaptive", "adapts", "education", "tutoring", "air traffic"),
        "systems that adapt to users' measured mental state, including in learning",
    ),
}

ROUTING_ORDER = ["neurofeedback", "decoding", "applications", "load", "foundations"]
DISPLAY_ORDER = ["foundations", "load", "decoding", "neurofeedback", "applications"]

SECTION_PROMPT = """You are writing ONE section of a literature review on "{topic}".
Section: "{heading}" ({description}).

Rules:
- Use ONLY the papers below. Cite with bracketed numbers matching the index: [3] or [3, 7].
- Cite a paper for a claim only if that paper's own line states it. Never cite a
  review, theory or tutorial paper as evidence for an empirical result.
- Do not invent facts, numbers, or firsts ("first", "seminal", "for decades")
  unless a paper's line says so.
- If a line says "not stated", write "not reported", never "did not".
- Neurofeedback is closed-loop training that rewards users for modulating their own
  brain activity. Distinguish it from adaptive scheduling of instruction, which
  changes what or when material is presented.
- Write 120-220 words of connected prose. No heading, no bullet points, no
  research-gaps discussion. Mention every paper below at least once if you can.

Papers for this section:
{papers_block}
"""


def _short(value, n=200):
    value = str(value or "not stated")
    return value if len(value) <= n else value[:n] + "..."


def _format_line(i, p):
    return (
        f"[{i}] {p.get('title', 'Untitled')} ({p.get('year') or 'n.d.'}) | "
        f"n: {_short(p.get('sample_size'), 40)} | "
        f"objective: {_short(p.get('objective'), 120)} | "
        f"findings: {_short(p.get('key_findings'), 200)} | "
        f"limitations: {_short(p.get('limitations'), 120)}"
    )


def _format_references(extracted):
    lines = []
    for i, p in enumerate(extracted, start=1):
        authors = p.get("authors") or []
        author_str = ", ".join(authors[:6]) + (" et al." if len(authors) > 6 else "")
        author_str = author_str or "Unknown authors"
        doi_part = f" doi:{p['doi']}" if p.get("doi") else ""
        lines.append(f"[{i}] {author_str} ({p.get('year') or 'n.d.'}). {p['title']}.{doi_part}")
    return "\n".join(lines)


def render_gaps(gaps):
    """Research Gaps section built in code from gap_analysis, never by the LLM."""
    rank = {"high": 0, "medium": 1, "low": 2}
    present = sorted((g for g in gaps if g.get("present")),
                     key=lambda g: rank.get(str(g.get("severity")).lower(), 3))
    absent = [g for g in gaps if g.get("present") is False]
    unknown = [g for g in gaps if g.get("present") is None]

    out = ["## Research Gaps", "",
           "*Based on abstract-level extraction: a gap means the extracted summaries do "
           "not state the item, not that the literature lacks it. Verify against full "
           "texts before relying on any item.*", ""]
    for n, g in enumerate(present, start=1):
        out.append(f"{n}. **{g['category']}** (severity: {g.get('severity', 'n/a')}). {g.get('evidence', '')}")
    if not present:
        out.append("No gaps were flagged as present.")
    if absent:
        out += ["", "**Checked and not flagged as a gap:**"]
        out += [f"- {g['category']}. {g.get('evidence', '')}" for g in absent]
    if unknown:
        out += ["", "**Could not be assessed (analysis failed):**"]
        out += [f"- {g['category']}" for g in unknown]
    return "\n".join(out)


def _route_papers(extracted):
    """Assign each paper (original 1-based index) to exactly one section."""
    routed = {key: [] for key in SECTIONS}
    for i, p in enumerate(extracted, start=1):
        title = (p.get("title") or "").lower()
        target = "foundations"  # fallback for anything unmatched
        for key in ROUTING_ORDER:
            if any(kw in title for kw in SECTIONS[key][1]):
                target = key
                break
        routed[target].append((i, p))
    return routed


def _write_section(llm, topic, key, papers):
    """One section = one or more small calls. Raises if a call returns no text."""
    heading, _, description = SECTIONS[key]
    chunks = [papers[k:k + MAX_PAPERS_PER_CALL] for k in range(0, len(papers), MAX_PAPERS_PER_CALL)]
    pieces = []
    for chunk in chunks:
        prompt = SECTION_PROMPT.format(
            topic=topic, heading=heading, description=description,
            papers_block="\n".join(_format_line(i, p) for i, p in chunk),
        )
        last_error = None
        for attempt in range(2):
            resp = None
            try:
                resp = invoke_with_retry(llm, prompt)
                text = (resp.content or "").strip()
                if not text:
                    meta = getattr(resp, "response_metadata", None) or {}
                    raise ValueError(f"empty output (finish_reason={meta.get('finish_reason')})")
                pieces.append(text)
                last_error = None
                break
            except Exception as e:
                last_error = e
                print(f"  [warn] section '{heading}', attempt {attempt + 1}: {e}")
        if last_error is not None:
            raise last_error
        time.sleep(PAUSE_S)
    return "\n\n".join(pieces)


def write_literature_review(extracted, gaps, topic):
    llm = get_llm(temperature=0.3, max_tokens=3000)
    routed = _route_papers(extracted)

    parts = []
    failed = []
    for key in DISPLAY_ORDER:
        papers = routed[key]
        if not papers:
            continue
        heading = SECTIONS[key][0]
        print(f"  writing section: {heading} ({len(papers)} papers)")
        try:
            body = _write_section(llm, topic, key, papers)
            parts.append(f"## {heading}\n\n{body}")
        except Exception as e:
            failed.append(heading)
            ids = ", ".join(str(i) for i, _ in papers)
            parts.append(
                f"## {heading}\n\n*[Section not generated: {e}. "
                f"Papers routed here: {ids}.]*"
            )

    if failed:
        print(f"  WARNING: {len(failed)} section(s) failed: {', '.join(failed)}")

    review_text = "\n\n".join(parts) + "\n\n" + render_gaps(gaps)
    return review_text, _format_references(extracted)


def _parse_citations(text):
    """Return every cited index from [3], [3, 7] and [3-5] style markers."""
    cited = set()
    for group in re.findall(r"\[([\d,\s\u2013\-]+)\]", text):
        for part in re.split(r"[,\s]+", group.strip()):
            if not part:
                continue
            m = re.fullmatch(r"(\d+)[\u2013\-](\d+)", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                if a <= b and b - a < 50:
                    cited.update(range(a, b + 1))
            elif part.isdigit():
                cited.add(int(part))
    return cited


def verify_citations(review_text, extracted):
    cited = _parse_citations(review_text)
    valid_range = set(range(1, len(extracted) + 1))
    invalid = sorted(cited - valid_range)
    never_cited = sorted(valid_range - cited)

    return {
        "all_citations_valid": len(invalid) == 0,
        "invalid_citation_indices": invalid,
        "papers_never_cited": never_cited,
        "total_citations_found": len(cited),
        "total_papers": len(extracted),
    }