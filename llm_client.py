import random
import re
import time

import config
from langchain_groq import ChatGroq

try:
    from groq import APIConnectionError, APITimeoutError
    NETWORK_ERRORS = (APIConnectionError, APITimeoutError)
except ImportError:  # groq SDK not importable: fall back to name matching below
    NETWORK_ERRORS = ()

# A rate-limit wait longer than this almost always means a daily quota (TPD)
# is used up, so sleeping won't help. Fail fast instead.
MAX_RATE_WAIT_S = 90


def get_llm(temperature: float = 0.2, max_tokens: int = 2500, reasoning_effort: str = "low"):
    """gpt-oss is a reasoning model: reasoning tokens count against max_tokens.
    Low effort plus a real cap avoids the 'empty content, finish_reason=length' failure.
    Raise max_tokens for long outputs (e.g. review sections)."""
    kwargs = dict(
        model=config.MODEL_NAME,
        api_key=config.GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=60,
        max_retries=0,  # we do our own retrying in invoke_with_retry
    )
    try:
        return ChatGroq(reasoning_effort=reasoning_effort, **kwargs)
    except Exception:
        # Older langchain-groq versions don't accept reasoning_effort.
        return ChatGroq(**kwargs)


def _retry_wait_seconds(msg, attempt):
    """Read Groq's 'try again in X' hint; fall back to exponential backoff."""
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", msg)
    if m:
        minutes = int(m.group(1) or 0)
        value = float(m.group(2))
        seconds = value / 1000 if m.group(3) == "ms" else value
        return minutes * 60 + seconds + 1.0
    return min(2 ** attempt, 30)


def _is_network_error(e):
    if NETWORK_ERRORS and isinstance(e, NETWORK_ERRORS):
        return True
    name = type(e).__name__
    return name in ("APIConnectionError", "APITimeoutError", "ConnectError", "ReadTimeout")


def invoke_with_retry(llm, prompt, max_retries=6):
    """llm.invoke that retries on network errors and short 429 rate limits.
    Fails fast (raises) when a rate-limit wait is too long to be worth sleeping."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            msg = str(e)

            if _is_network_error(e):
                wait = min(60, 5 * 2 ** attempt) + random.random()
                print(f"    [network] {type(e).__name__}; retrying in {wait:.0f}s "
                      f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            if "429" in msg or "rate_limit" in msg:
                wait = _retry_wait_seconds(msg, attempt)
                if wait > MAX_RATE_WAIT_S:
                    raise RuntimeError(
                        f"Rate limit wait of {wait:.0f}s is too long; your daily quota "
                        "is probably used up. Check the Groq console, then rerun."
                    ) from e
                print(f"    [rate limit] waiting {wait:.1f}s "
                      f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            raise
    raise RuntimeError("LLM call failed after retries; check your network and quota")