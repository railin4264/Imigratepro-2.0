"""Integration with USCIS's official Case Status API (developer.uscis.gov,
"Torch Platform") -- OAuth2 client-credentials flow, one receipt number per
call. This is a *read-only* status check: it cannot file anything, cannot
list a firm's cases in bulk, and doesn't push notifications -- the caller
has to ask again to see if something changed (see the endpoint that calls
this for how often that's reasonable given the documented daily quota).

Requires USCIS_API_CLIENT_ID/SECRET (see core/config.py). Without them,
is_configured() is False and the feature stays out of the UI entirely --
same degradation pattern as the Anthropic integration. Getting real
credentials is not something this code can do for you: it requires
registering a developer app at developer.uscis.gov, running the sandbox
for 5+ consecutive days, and USCIS granting production access on request
(developersupport@uscis.dhs.gov). Sandbox works immediately with USCIS's
published staging receipt numbers and needs no separate registration for
the sandbox tier itself, only for eventually moving to production.
"""

import time

import httpx

from app.core.config import settings

_TOKEN_EXPIRY_BUFFER_SECONDS = 60

# Module-level cache: one client-credentials token shared by every request in
# this process, refreshed a little before it actually expires. Mirrors the
# in-memory-is-fine posture already used for rate limiting (see
# core/rate_limit.py) -- a single backend instance is the deployment target
# this app assumes throughout.
_cached_token: str | None = None
_cached_token_expires_at: float = 0.0


class USCISAPIError(RuntimeError):
    """Raised for anything the caller should show as 'couldn't check status
    right now' -- auth failures, USCIS-side errors, network errors, and
    receipt numbers USCIS doesn't recognize all land here rather than as
    unrelated exception types the endpoint would have to know about."""


def is_configured() -> bool:
    return bool(settings.USCIS_API_CLIENT_ID and settings.USCIS_API_CLIENT_SECRET)


def _fetch_new_token() -> str:
    response = httpx.post(
        settings.USCIS_API_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.USCIS_API_CLIENT_ID,
            "client_secret": settings.USCIS_API_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15.0,
    )
    if response.status_code != 200:
        raise USCISAPIError(f"USCIS authentication failed ({response.status_code})")

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise USCISAPIError("USCIS authentication response had no access_token")

    global _cached_token, _cached_token_expires_at
    _cached_token = token
    expires_in = payload.get("expires_in", 3600)
    _cached_token_expires_at = time.time() + int(expires_in) - _TOKEN_EXPIRY_BUFFER_SECONDS
    return token


def _get_access_token(force_refresh: bool = False) -> str:
    if not force_refresh and _cached_token and time.time() < _cached_token_expires_at:
        return _cached_token
    return _fetch_new_token()


def get_case_status(receipt_number: str) -> dict:
    """Fetch the current status for one receipt number. Returns the raw
    JSON body from USCIS (shape varies slightly for IOE-prefixed receipt
    numbers per USCIS's own schema split) -- callers store/display it as-is
    rather than this module asserting a fixed internal structure it can't
    fully verify without production access to see real responses."""

    if not is_configured():
        raise USCISAPIError("USCIS_API_CLIENT_ID/USCIS_API_CLIENT_SECRET are not configured")

    receipt_number = receipt_number.strip().upper()
    if not receipt_number:
        raise USCISAPIError("Receipt number is required")

    url = f"{settings.USCIS_API_BASE_URL}/case-status/{receipt_number}"

    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        response = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15.0)

        if response.status_code == 401 and attempt == 1:
            continue  # token may have just expired server-side; refresh once and retry
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            # Also the response USCIS gives for receipt numbers covered by the
            # 8 U.S.C. 1367 confidentiality protections -- there's no way to
            # tell the two cases apart from the response alone.
            raise USCISAPIError(f"USCIS has no record of receipt number '{receipt_number}'")
        if response.status_code == 422:
            raise USCISAPIError(
                "Receipt number format is invalid: it must be 3 letters followed by 10 digits (e.g. EAC9999103403)"
            )
        if response.status_code == 429:
            # Sandbox caps at 5 TPS / 1,000 requests per day; production is
            # 10 TPS / 400,000 per day (resets midnight EST). Either way this
            # is transient -- worth a retry later, not a retry-now loop.
            raise USCISAPIError("USCIS rate limit exceeded for this app -- try again shortly")
        if response.status_code == 503:
            raise USCISAPIError(
                "USCIS Case Status service is unavailable right now (their maintenance window is "
                "M-F 7:00AM-8:00PM EST) -- try again later"
            )
        raise USCISAPIError(f"USCIS case status check failed ({response.status_code})")

    raise USCISAPIError("USCIS authentication failed after retrying with a fresh token")
