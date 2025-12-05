# tests/test_csv_store.py
import os
import tempfile

from pydantic import BaseModel
from storage.csv_store import CsvRepository


class DummyModel(BaseModel):
    id: str
    name: str
    meta: dict | None = None


def test_csv_repository_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "dummy.csv")
        repo = CsvRepository(
            csv_path=path,
            model_cls=DummyModel,
            required_columns=["id", "name", "meta"],
        )

        m1 = DummyModel(id="1", name="Test", meta={"a": 1})
        m2 = DummyModel(id="2", name="Foo", meta={"b": 2})

        repo.append(m1)
        repo.append(m2)

        all_rows = repo.load_all()
        assert len(all_rows) == 2
        assert all_rows[0].meta["a"] == 1

        filtered = repo.load_by_filter(id="2")
        assert len(filtered) == 1
        assert filtered[0].name == "Foo"
