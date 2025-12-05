# models/__init__.py
"""
Models package for AutoTARA-RAG.

Contains all Pydantic schemas used across:
- Assets
- Damage scenarios
- Impact ratings
- Threat scenarios
- Vulnerability references and attack paths
- Attack feasibility
- Risk values
- RAG reference entities (CVE/CWE/CAPEC/ATT&CK/ATM)
"""

from .schemas import (  # noqa: F401
    CyberProperty,
    Interface,
    SoftwareComponent,
    Asset,
    DamageScenario,
    ImpactRating,
    ThreatScenario,
    VulnerabilityRef,
    AttackPath,
    AttackFeasibility,
    RiskValue,
    VulnerabilityReference,
    WeaknessReference,
    AttackPatternReference,
    TechniqueReference,
    AutomotiveThreatReference,
)
