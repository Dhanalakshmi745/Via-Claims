import pytest

from claimvision_ai.testing import HashingEmbedder


@pytest.fixture()
def fake_embedder():
    return HashingEmbedder()