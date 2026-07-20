"""Shared client config for every Anthropic call this app makes. document_ai,
rfe_ai, and form_review_ai each used to build their own anthropic.Anthropic(
api_key=...) with no explicit timeout or retry policy, relying entirely on
the SDK's defaults -- a hung upstream request then blocks a real request
thread indefinitely, and a request that fails on a single transient 5xx has
no recovery. Centralized here so the three stay consistent and a future
policy change doesn't mean editing three files."""

import anthropic

from app.core.config import settings

# connect/write/pool stay tight -- a slow TCP handshake or a stalled upload
# points at a network problem, not model latency, and should fail fast.
# `read` is generous because "adaptive" extended-thinking calls (used by all
# three services) can legitimately run long.
REQUEST_TIMEOUT = anthropic.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)

# The SDK only retries its own retryable statuses (429/5xx/connection
# errors) -- a 400 or a model refusal is never retried, since retrying
# wouldn't change the outcome.
MAX_RETRIES = 3


def build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )
