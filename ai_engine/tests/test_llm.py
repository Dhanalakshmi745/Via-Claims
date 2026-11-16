import pytest

from claimvision_ai.llm import create_llm_client


def test_unsupported_provider_is_rejected():
    with pytest.raises(ValueError):
        create_llm_client("not-a-provider", "some-key")


def test_missing_api_key_is_rejected():
    with pytest.raises(ValueError):
        create_llm_client("gemini", "")