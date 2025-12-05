# tests/test_rag_vector_store.py
import os
import tempfile
import numpy as np

from rag.vector_store import VectorStore, Document


class DummyEmbResp:
    def __init__(self, n, dim=4):
        self.data = []
        for _ in range(n):
            self.data.append(type("obj", (), {"embedding": [0.1] * dim}))


class DummyClient:
    def embeddings(self):
        return self

    def create(self, model, input):
        return DummyEmbResp(len(input))


def test_vector_store_add_and_search(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        idx_path = os.path.join(tmp, "index")

        vs = VectorStore(idx_path)

        # Monkeypatch client
        vs.client.embeddings.create = lambda model, input: DummyEmbResp(len(input))

        docs = [
            Document(
                id="DOC1",
                source="STANDARD",
                type="TEXT",
                title="ISO 21434 brake systems",
                body="Brake-by-wire cybersecurity requirements.",
                metadata={"filename": "iso21434_brake.txt"},
            ),
            Document(
                id="DOC2",
                source="NVD",
                type="CVE",
                title="CVE-2023-0001",
                body="Buffer overflow in brake ECU firmware.",
                metadata={"cve_id": "CVE-2023-0001"},
            ),
        ]
        vs.add_documents(docs)

        results = vs.similarity_search("brake ECU vulnerabilities", k=1)
        assert len(results) == 1
        assert results[0].id in {"DOC1", "DOC2"}
