import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "normalization",
    Path(__file__).resolve().parents[1] / "services" / "normalization.py",
)
normalization = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(normalization)
normalize = normalization.normalize


def test_attack_potential_normalization_handles_common_variants():
    assert normalize("attackPotential", "Moderate") == "medium"
    assert normalize("attackPotential", "Very Low") == "very low"
    assert normalize("attackPotential", "HIGH") == "high"
