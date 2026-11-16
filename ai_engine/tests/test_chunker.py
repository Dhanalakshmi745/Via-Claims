import pytest

from claimvision_ai.chunker import chunk_text


def numbered_text(count: int = 200) -> str:
    return " ".join(f"Sentence {i} describes the incident." for i in range(count))


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_is_a_single_chunk():
    assert chunk_text("Short report.") == ["Short report."]


def test_chunks_respect_max_size():
    chunks = chunk_text(numbered_text(), max_chars=300, overlap=60)

    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)


def test_no_sentence_is_lost():
    chunks = chunk_text(numbered_text(), max_chars=300, overlap=60)

    for i in range(200):
        sentence = f"Sentence {i} describes the incident."
        assert any(sentence in chunk for chunk in chunks), sentence


def test_invalid_parameters_raise_error():
    with pytest.raises(ValueError):
        chunk_text("text", max_chars=0)
    with pytest.raises(ValueError):
        chunk_text("text", max_chars=100, overlap=60)


def test_chunks_do_not_start_mid_word():
    text = numbered_text()
    words = set(text.split())
    chunks = chunk_text(text, max_chars=300, overlap=60)

    assert all(chunk.split()[0] in words for chunk in chunks)