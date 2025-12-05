# services/__init__.py
"""
Service layer for AutoTARA-RAG.

Each module implements a TARA pipeline stage:

1. asset_extraction      → SysML → assets.csv
2. damage_scenarios      → assets.csv → damage_scenarios.csv
3. impact_rating         → damage_scenarios.csv → impact_rating.csv
4. threat_scenarios      → damage_scenarios.csv → threat_scenarios.csv
5. vuln_attack_paths     → threat_scenarios.csv → attack_paths.csv
6. attack_feasibility    → attack_paths.csv → attack_feasibilities.csv
7. risk_values           → all above → risk_values.csv
"""

from .asset_extraction import run_asset_extraction  # noqa: F401
from .damage_scenarios import run_damage_stage  # noqa: F401
from .impact_rating import run_impact_stage  # noqa: F401
from .threat_scenarios import run_threat_stage  # noqa: F401
from .vuln_attack_paths import run_vuln_attack_paths_stage  # noqa: F401
from .attack_feasibility import run_attack_feasibility_stage  # noqa: F401
from .risk_values import run_risk_values_stage  # noqa: F401
