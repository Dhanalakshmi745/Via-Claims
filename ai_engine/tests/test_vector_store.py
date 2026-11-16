import pytest

from claimvision_ai.vector_store import VectorStore


@pytest.fixture()
def store(tmp_path, fake_embedder):
    return VectorStore(persist_directory=str(tmp_path / "chroma"), embedder=fake_embedder)


def index_sample_documents(store):
    store.index_document(
        document_id=1,
        claim_id=10,
        document_type="POLICE_REPORT",
        chunks=[
            "The driver of the Honda City reported being rear-ended at the Adyar signal.",
            "Witness statement says the other vehicle was speeding and braked late.",
        ],
    )
    store.index_document(
        document_id=2,
        claim_id=10,
        document_type="REPAIR_ESTIMATE",
        chunks=["Estimate for rear bumper replacement and paint work totals forty five thousand rupees."],
    )
    store.index_document(
        document_id=3,
        claim_id=20,
        document_type="INVOICE",
        chunks=["Hospital invoice for consultation and medicines for the claimant."],
    )


def test_index_returns_number_of_chunks(store):
    count = store.index_document(
        document_id=1, claim_id=10, document_type="OTHER", chunks=["first chunk", "second chunk"]
    )
    assert count == 2


def test_search_finds_most_relevant_chunk(store):
    index_sample_documents(store)

    results = store.search("rear bumper replacement estimate")

    assert results[0].document_id == 2
    assert results[0].document_type == "REPAIR_ESTIMATE"


def test_search_can_be_limited_to_one_claim(store):
    index_sample_documents(store)

    results = store.search("hospital invoice medicines", claim_id=10)

    assert results
    assert all(result.claim_id == 10 for result in results)


def test_reindexing_replaces_old_chunks(store):
    store.index_document(
        document_id=1, claim_id=10, document_type="OTHER", chunks=["driver one", "driver two"]
    )
    store.index_document(document_id=1, claim_id=10, document_type="OTHER", chunks=["driver only"])

    assert len(store.search("driver", top_k=10)) == 1


def test_deleted_document_no_longer_appears_in_results(store):
    index_sample_documents(store)

    store.delete_document(2)
    results = store.search("rear bumper replacement estimate", top_k=10)

    assert all(result.document_id != 2 for result in results)


def test_search_on_empty_store_returns_nothing(store):
    assert store.search("anything at all") == []