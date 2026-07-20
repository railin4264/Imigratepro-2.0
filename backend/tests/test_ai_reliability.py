"""The three AI services (document_ai, rfe_ai, form_review_ai) used to each
build their own anthropic.Anthropic(api_key=...) with the SDK's bare
defaults -- no explicit timeout, so a hung upstream request could block a
request thread indefinitely, and no tuned retry policy. build_client()
centralizes a single reasonable policy; these tests pin down what that
policy actually is so a future edit can't silently drop it."""

from app.services.ai_reliability import MAX_RETRIES, REQUEST_TIMEOUT, build_client


def test_build_client_sets_explicit_timeout_and_retries(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ANTHROPIC_API_KEY", "test-key")
    client = build_client()
    assert client.timeout == REQUEST_TIMEOUT
    assert client.max_retries == MAX_RETRIES


def test_read_timeout_is_generous_but_connect_is_tight():
    # A slow TCP handshake points at a network problem and should fail
    # fast; the "adaptive" extended-thinking calls all three services use
    # can legitimately run long, so the read timeout needs headroom for that.
    assert REQUEST_TIMEOUT.connect < REQUEST_TIMEOUT.read


def test_retries_are_configured_above_the_sdk_default_of_two():
    assert MAX_RETRIES > 2
