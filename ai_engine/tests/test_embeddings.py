import pytest

from claimvision_ai.embeddings import SentenceTransformerEmbedder


@pytest.fixture(scope="module")
def embedder():
    return SentenceTransformerEmbedder()


def similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def test_vectors_have_expected_size(embedder):
    vectors = embedder.embed(["The car was damaged.", "Another sentence."])

    assert len(vectors) == 2
    assert len(vectors[0]) == 384


def test_similar_meaning_scores_higher_than_unrelated_text(embedder):
    rear_ended, hit_from_behind, recipe = embedder.embed(
        [
            "The car was hit from behind at a traffic light.",
            "A vehicle was rear-ended while stopped at a signal.",
            "The recipe needs two cups of flour and one egg.",
        ]
    )

    assert similarity(rear_ended, hit_from_behind) > similarity(rear_ended, recipe)