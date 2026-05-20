"""Test configuration — fixtures, markers, credential detection."""
import os
import pytest


def has_hedera_creds() -> bool:
    return bool(os.environ.get("HEDERA_OPERATOR_ID")) and bool(
        os.environ.get("HEDERA_OPERATOR_KEY")
    )


def has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def has_twitter_creds() -> bool:
    return bool(os.environ.get("twitter_api_key")) or bool(
        os.environ.get("TWITTER_API_KEY")
    )


skip_if_no_hedera = pytest.mark.skipif(
    not has_hedera_creds(),
    reason="HEDERA_OPERATOR_ID / HEDERA_OPERATOR_KEY not set",
)

skip_if_no_openai = pytest.mark.skipif(
    not has_openai_key(),
    reason="OPENAI_API_KEY not set",
)

skip_if_no_twitter = pytest.mark.skipif(
    not has_twitter_creds(),
    reason="Twitter credentials not set",
)
