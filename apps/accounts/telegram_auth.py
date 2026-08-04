"""
Server-side verification of Telegram Mini App initData.
Algorithm: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
Pure stdlib — no Django/aiogram imports — so it's cheap to unit test in isolation.
"""

import hashlib
import hmac
import time
from urllib.parse import parse_qsl

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60  # 24h — anti-replay for a leaked initData string


class InitDataError(Exception):
    """Raised when initData is missing, malformed, unsigned, or stale."""


def verify_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = MAX_AUTH_AGE_SECONDS,
) -> dict[str, str]:
    """
    Verifies the HMAC-SHA256 signature of a Telegram WebApp initData string.
    Returns the parsed key/value pairs on success (values are still raw strings —
    e.g. "user" is a JSON-encoded string the caller must json.loads()).
    Raises InitDataError on any failure.
    """
    if not init_data:
        raise InitDataError("empty initData")

    try:
        pairs = parse_qsl(init_data, strict_parsing=True)
    except ValueError as exc:
        raise InitDataError("malformed initData") from exc
    data = dict(pairs)

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise InitDataError("missing hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))

    # secret_key = HMAC_SHA256(key="WebAppData", data=bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InitDataError("signature mismatch")

    auth_date = data.get("auth_date")
    if not auth_date or not auth_date.isdigit():
        raise InitDataError("missing/invalid auth_date")
    if time.time() - int(auth_date) > max_age_seconds:
        raise InitDataError("initData expired")

    return data
