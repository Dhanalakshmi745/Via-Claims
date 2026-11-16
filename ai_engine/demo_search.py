import tempfile

from claimvision_ai.chunker import chunk_text
from claimvision_ai.embeddings import SentenceTransformerEmbedder
from claimvision_ai.vector_store import VectorStore

REPORT = """
On 15 June the insured vehicle, a Honda City, was stopped at the Adyar signal when a lorry
approached from behind and could not brake in time. The rear bumper and boot lid were crushed.

The lorry driver admitted he was looking at his phone. A traffic constable recorded the
statement and noted wet road conditions after morning rain.

The insured and a passenger complained of neck pain and were taken to a nearby hospital
for observation and discharged the same evening.
"""

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
    store = VectorStore(folder, SentenceTransformerEmbedder())
    chunks = chunk_text(REPORT, max_chars=300, overlap=50)
    store.index_document(document_id=1, claim_id=1, document_type="POLICE_REPORT", chunks=chunks)

    for question in ["Was anyone injured?", "What caused the collision?", "What was the weather?"]:
        best = store.search(question, claim_id=1, top_k=1)[0]
        print(f"\nQ: {question}\n   distance={best.distance:.3f}\n   {best.text[:110]}...")