import os

# Broadened so real matches survive filtering. Your narrower angle
# (closed-loop spaced repetition) is covered by the gap taxonomy and queries.
TOPIC = "EEG-based passive brain-computer interfaces for adaptive learning"

# present=true always means "this gap EXISTS in the literature".
# The first row is computed in code from each paper's sample_size field,
# so its wording must keep starting with "Small subject cohorts".
GAP_TAXONOMY = [
    "Small subject cohorts (n<15)",
    "Lab-only / controlled settings, not real-world or naturalistic deployment",
    "No EEG-driven closed-loop adaptation of instruction (studies only monitor or decode EEG, or use neurofeedback without adapting what or when material is presented)",
    "No study uses or validates consumer-grade dry EEG (e.g. Muse) for learning",
    "Individual variability in theta/alpha response not addressed",
    "No long-term / multi-session retention outcomes (only immediate recall tested)",
    "Confounds (fatigue, caffeine, mood, time-of-day) not controlled or reported",
    "No comparison against a fixed-interval or non-adaptive baseline",
    "No adaptive scheduling policy learned from delayed recall feedback (e.g. bandit / RL)",
]

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = "openai/gpt-oss-20b"

MAX_PAPERS = 30  # keeps gap-analysis and synthesis prompts under the 8k TPM limit

OUTPUT_MD = "literature_review.md"