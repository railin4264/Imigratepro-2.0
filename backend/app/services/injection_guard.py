"""Defense for the places this app's AI features interpolate client-controlled
text into a prompt: an RFE notice pasted by staff (which may itself quote or
paraphrase adversarial content) and client-entered form field values sourced
from the public wizard. Neither should ever be able to redirect what the
model does. This isn't the only defense -- every AI call in this app already
constrains output to a fixed JSON schema and requires human review before
anything downstream trusts it -- but it closes the direct-instruction-
injection path and gives something to alert on."""

import logging
import re

logger = logging.getLogger("migratepro.ai")

UNTRUSTED_OPEN = "<<<UNTRUSTED_USER_DATA>>>"
UNTRUSTED_CLOSE = "<<<END_UNTRUSTED_USER_DATA>>>"

_SUSPICIOUS_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above)", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"^\s*system\s*:", re.I | re.M),
    re.compile(r"\bnew\s+instructions?\s*:", re.I),
    re.compile(r"reveal\s+(your|the)\s+(system\s+)?prompt", re.I),
]


def wrap_untrusted(text: str) -> str:
    """Delimits text that came from a client/preparer paste so the prompt
    template's surrounding instructions can tell the model that anything
    between these markers is data to analyze, never a command."""
    return f"{UNTRUSTED_OPEN}\n{text}\n{UNTRUSTED_CLOSE}"


def looks_like_injection_attempt(text: str) -> bool:
    """Heuristic only -- a signal to log, not a hard block. An RFE notice or
    form answer that happens to match one of these phrases isn't unheard of
    (a form field could legitimately contain the word "system"), and every
    AI call in this app already forces structured JSON output plus a
    mandatory human review before anything downstream trusts it."""
    return any(pattern.search(text) for pattern in _SUSPICIOUS_PATTERNS)


def check_and_wrap(text: str, *, context: str) -> str:
    """Combines the two: logs a warning (for ops visibility, not a block --
    see looks_like_injection_attempt) and returns the delimited text ready
    to drop into a prompt template."""
    if looks_like_injection_attempt(text):
        logger.warning("Possible prompt injection pattern detected in %s", context)
    return wrap_untrusted(text)
