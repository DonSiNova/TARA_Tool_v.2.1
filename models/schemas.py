# models/schemas.py
"""
Pydantic models for the AutoTARA-RAG pipeline.

These models define the core entities and their JSON/CSV structures:
- Asset (from SysML)
- DamageScenario
- ImpactRating
- ThreatScenario
- VulnerabilityRef and AttackPath
- AttackFeasibility
- RiskValue
- RAG reference data entities (CVE, CWE, CAPEC, ATT&CK, ATM)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# Common types
# -------------------------------------------------------------------

CyberProperty = Literal[
    "Confidentiality",
    "Integrity",
    "Availability",
    "Authenticity",
    "Non-Repudiation",
    "Authorization",
]


class Interface(BaseModel):
    """
    Represents an interface of an asset (e.g. CAN, LIN, Ethernet, Diagnostics).
    """

    type: str = Field(..., description="Interface type, e.g., CAN, LIN, Ethernet, UDS")
    direction: Literal["in", "out", "inout"] = Field(
        "inout",
        description="Direction of signal flow for this interface",
    )
    exposure: str = Field(
        "",
        description="Exposure description, e.g., 'vehicle-internal', 'external-remote', 'diagnostic'",
    )


class SoftwareComponent(BaseModel):
    """
    A software component forming part of the asset's software stack.
    """

    name: str = Field(..., description="Component name, e.g., OS kernel, CAN stack")
    version: Optional[str] = Field(
        None,
        description="Version string if known, e.g., '1.0.3'",
    )
    vendor: Optional[str] = Field(
        None,
        description="Vendor or supplier, if known",
    )
    category: Optional[str] = Field(
        None,
        description="Category such as 'OS', 'Middleware', 'Application', 'Bootloader', 'Firmware'",
    )


# -------------------------------------------------------------------
# Core TARA entities
# -------------------------------------------------------------------


class Asset(BaseModel):
    """
    Asset extracted from SysML, as defined by ISO/SAE 21434.
    """

    assetTag: str = Field(
        "",
        description="Friendly sequential asset tag (A-0001...) used for cross-stage linking.",
    )
    assetId: str = Field(..., description="Unique asset identifier (primary key).")
    itemId: str = Field(..., description="Identifier of the SysML item/block this asset relates to.")
    type: Literal[
        "ECU",
        "Sensor",
        "Network",
        "ExternalActor",
        "Signal",
        "Power",
        "Component",
    ] = Field(..., description="Type of asset within the system.")
    description: str = Field(..., description="Short description of the asset and its role.")
    location: Optional[str] = Field(
        "",
        description="Physical or logical location of the asset in the vehicle/system.",
    )
    cyberProperties: List[CyberProperty] = Field(
        default_factory=list,
        description="List of cybersecurity properties for which this asset is relevant.",
    )
    interfaces: List[Interface] = Field(
        default_factory=list,
        description="Interfaces exposing or connecting this asset.",
    )
    softwareStack: List[SoftwareComponent] = Field(
        default_factory=list,
        description="Software elements running on / associated with this asset.",
    )


class DamageScenario(BaseModel):
    """
    One-sentence damage scenario for a given asset + cyber property,
    generated using the damage_scenario prompt.
    """

    damageId: str = Field(..., description="Unique identifier for the damage scenario (primary key).")
    assetId: str = Field(..., description="Foreign key: referenced Asset.assetId.")
    assetTag: str = Field(
        ...,
        description="Friendly Asset.assetTag used for linking downstream stages.",
    )
    cyber_property: CyberProperty = Field(
        ...,
        description="Cybersecurity property (C/I/A/Auth/NR/Authz) to which this damage scenario relates.",
    )
    one_sentence: str = Field(
        ...,
        description="Final one-sentence damage scenario between !!!! markers.",
    )
    raw_llm_output: str = Field(
        ...,
        description="Full raw text returned by the LLM for traceability and auditing.",
    )
    stakeholder: Literal["Road User", "OEM", "Both"] = Field(
        "Road User",
        description="Stakeholder for which the damage scenario is evaluated.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp at which this damage scenario was generated.",
    )


class ImpactRating(BaseModel):
    """
    Impact rating for a given damage scenario, based on SFOP for Road Users
    and RFOIP for OEM, returned by the impact_rating prompt.
    """

    impactId: str = Field(..., description="Unique identifier of the impact rating record (primary key).")
    damageId: str = Field(..., description="Foreign key: associated DamageScenario.damageId.")
    assetTag: str = Field(
        ...,
        description="Friendly asset tag for filtering/linking.",
    )
    stakeholder: Literal["Road User", "OEM", "Both"] = Field(
        ...,
        description="Stakeholder context for which this impact rating was derived.",
    )

    # Road User SFOP (Safety, Financial, Operational, Privacy)
    road_user_sfop: Optional[Dict[str, int]] = Field(
        default=None,
        description=(
            "Impact scores for the road user: "
            "{'safety': 0-3, 'financial': 0-3, 'operational': 0-3, 'privacy': 0-3}"
        ),
    )

    # OEM RFOIP (Reputation, Financial, Operational, IP)
    oem_rfoip: Optional[Dict[str, int]] = Field(
        default=None,
        description=(
            "Impact scores for the OEM: "
            "{'reputation': 0-3, 'financial': 0-3, 'operational': 0-3, 'ip': 0-3}"
        ),
    )

    raw_llm_output: str = Field(
        ...,
        description="Full raw text returned by the impact rating LLM call.",
    )


class ThreatScenario(BaseModel):
    """
    Threat scenario for a given damage scenario, produced by threat_scenario prompt.
    """

    threatId: str = Field(..., description="Unique identifier of the threat scenario (primary key).")
    damageId: str = Field(..., description="Foreign key: associated DamageScenario.damageId.")
    assetId: str = Field(..., description="Foreign key: associated Asset.assetId.")
    assetTag: str = Field(..., description="Friendly asset tag.")
    cyber_property: CyberProperty = Field(
        ...,
        description="Cybersecurity property associated with this threat scenario.",
    )
    one_sentence: str = Field(
        ...,
        description="Single-sentence threat scenario text produced in Step 3.",
    )
    attack_vectors: List[str] = Field(
        default_factory=list,
        description="List of applicable attack vectors (Network, Remote, Physical, Supply Chain, Production Line, Diagnostic).",
    )
    raw_llm_output: str = Field(
        ...,
        description="Full raw text returned by the threat scenario LLM call.",
    )


class VulnerabilityRef(BaseModel):
    """
    Vulnerability reference object used inside AttackPath,
    derived from the vulnerability & attack path stage.
    """

    backing: Literal["NVD", "potential_generated"] = Field(
        ...,
        description="If backed by real NVD data or a potential, generated path needing validation.",
    )
    cve_id: Optional[str] = Field(
        None,
        description="CVE identifier if NVD-backed, otherwise null.",
    )
    cwe_id: Optional[str] = Field(
        None,
        description="CWE identifier if mapped, otherwise null.",
    )
    component: str = Field(
        ...,
        description="Component name within the asset's software stack or system where vulnerability applies.",
    )
    cpe_candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description='List of {"cpe": "<CPE string>", "confidence": "HIGH/MEDIUM/LOW"} objects.',
    )
    weakness_family: str = Field(
        ...,
        description="High-level weakness family, e.g., 'auth_bypass', 'memory_corruption', 'insecure_diagnostic'.",
    )
    attack_vectors: List[str] = Field(
        default_factory=list,
        description="Applicable attack vectors inferred for this vulnerability.",
    )


class AttackPath(BaseModel):
    """
    Attack path describing ordered steps from initial vector to final impact
    for a given threat scenario, following vulnerability_attackpath prompt.
    """

    pathId: str = Field(..., description="Unique identifier for the attack path (primary key).")
    threatId: str = Field(..., description="Foreign key: associated ThreatScenario.threatId.")
    assetId: str = Field(..., description="Foreign key: associated Asset.assetId.")
    assetTag: str = Field(..., description="Friendly Asset.assetTag.")
    damageId: str = Field(..., description="Foreign key: associated DamageScenario.damageId.")

    vulnerabilities: List[VulnerabilityRef] = Field(
        default_factory=list,
        description="List of vulnerability references involved in this path.",
    )

    entry_vector: str = Field(
        ...,
        description="Entry vector for this path, one of the attack vector categories.",
    )
    backing: Literal["NVD-supported", "potential_generated"] = Field(
        ...,
        description="Indicates if this path is supported by real NVD CVEs or is a potential path.",
    )
    cve_id: Optional[str] = Field(
        None,
        description="Primary CVE ID backing this path, if any.",
    )
    cwe_id: Optional[str] = Field(
        None,
        description="Primary CWE ID associated with this path, if any.",
    )

    attck_techniques: List[str] = Field(
        default_factory=list,
        description="List of MITRE ATT&CK technique IDs, e.g., ['T1200', 'T1059.003'].",
    )
    capec_ids: List[str] = Field(
        default_factory=list,
        description="List of CAPEC IDs, e.g., ['CAPEC-123', 'CAPEC-456'].",
    )
    atm_ids: List[str] = Field(
        default_factory=list,
        description="List of Automotive Threat Matrix IDs.",
    )
    steps: List[str] = Field(
        default_factory=list,
        description="Ordered list of human-readable attacker steps (Step 1..N).",
    )

    raw_llm_output: str = Field(
        ...,
        description="Full raw text returned by the vulnerability+attack path LLM call.",
    )


class AttackFeasibility(BaseModel):
    """
    Attack feasibility evaluation for a threat and attack path,
    as produced by the attack_feasibility prompt.
    """

    feasibilityId: str = Field(..., description="Unique identifier for this feasibility record (primary key).")
    threatId: str = Field(..., description="Foreign key: associated ThreatScenario.threatId.")
    assetTag: str = Field(..., description="Friendly asset tag for filtering.")
    pathId: str = Field(..., description="Foreign key: associated AttackPath.pathId.")

    mappedCVE: List[str] = Field(
        default_factory=list,
        description="List of CVE IDs relevant to this feasibility assessment.",
    )
    cwe: List[str] = Field(
        default_factory=list,
        description="List of CWE IDs relevant to this feasibility assessment.",
    )

    elapsedTime_score: int = Field(
        ...,
        description="Elapsed Time score according to feasibility table.",
    )
    specialistExpertise_score: int = Field(
        ...,
        description="Specialist Expertise score according to feasibility table.",
    )
    knowledgeOfItem_score: int = Field(
        ...,
        description="Knowledge of Item score according to feasibility table.",
    )
    windowOfOpportunity_score: int = Field(
        ...,
        description="Window of Opportunity score according to feasibility table.",
    )
    equipmentRequired_score: int = Field(
        ...,
        description="Equipment Required score according to feasibility table.",
    )

    totalScore: int = Field(
        ...,
        description="Sum of all feasibility scores.",
    )
    attackPotential: Literal["Basic", "Enhanced Basic", "Moderate", "High", "Beyond high"] = Field(
        ...,
        description="Attack potential classification derived from totalScore.",
    )
    attackFeasibility: Literal["High", "Medium", "Low", "Very Low"] = Field(
        ...,
        description="Attack feasibility level derived from totalScore.",
    )

    raw_llm_output: str = Field(
        ...,
        description="Full raw text returned by the attack feasibility LLM call.",
    )


class RiskValue(BaseModel):
    """
    Final risk value record for a threat scenario and stakeholder,
    as produced by the risk_values prompt.
    """

    riskId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this risk record (primary key).",
    )
    threatId: str = Field(..., description="Foreign key: associated ThreatScenario.threatId.")
    assetTag: str = Field(..., description="Friendly asset tag for filtering.")
    stakeholder: Literal["Road User", "OEM"] = Field(
        ...,
        description="Stakeholder context under which this risk value is computed.",
    )
    impactCategory: Literal["severe", "serious", "moderate", "negligible"] = Field(
        ...,
        description="Final impact category derived from impact scores.",
    )
    attackPotential: Literal["very low", "low", "medium", "high"] = Field(
        ...,
        description="Attack potential classification as used in the risk matrix.",
    )
    riskValue: int = Field(
        ...,
        description="Numeric risk value from the risk matrix (1–5).",
    )
    justification: str = Field(
        ...,
        description="Short, rigorous explanation why this risk value was selected.",
    )


# -------------------------------------------------------------------
# RAG reference entities
# -------------------------------------------------------------------


class VulnerabilityReference(BaseModel):
    """
    Structured representation of an NVD CVE entry
    used as reference in RAG context.
    """

    cve_id: str = Field(..., description="CVE identifier.")
    description: str = Field(..., description="Summary description of the vulnerability.")
    cvss_score: float = Field(..., description="Primary CVSS score associated with this CVE.")
    cvss_vector: str = Field(..., description="CVSS vector string.")
    cwe_ids: List[str] = Field(default_factory=list, description="List of associated CWE IDs.")
    cpe_matches: List[str] = Field(
        default_factory=list,
        description="List of compatible CPE strings from NVD match data.",
    )


class WeaknessReference(BaseModel):
    """
    Structured representation of a CWE entry.
    """

    cwe_id: str = Field(..., description="CWE identifier.")
    description: str = Field(..., description="Textual description of the weakness.")
    weakness_family: str = Field(
        ...,
        description="High-level weakness family (e.g., 'Injection', 'Memory Corruption').",
    )


class AttackPatternReference(BaseModel):
    """
    Structured representation of a CAPEC attack pattern.
    """

    capec_id: str = Field(..., description="CAPEC identifier, e.g., 'CAPEC-123'.")
    name: str = Field(..., description="Name of the CAPEC attack pattern.")
    description: str = Field(..., description="Summary description of the attack pattern.")


class TechniqueReference(BaseModel):
    """
    Structured representation of a MITRE ATT&CK technique.
    """

    attack_id: str = Field(..., description="ATT&CK technique ID, e.g., 'T1059.003'.")
    tactic: str = Field(..., description="ATT&CK tactic name.")
    technique: str = Field(..., description="Technique name.")
    description: str = Field(..., description="Summary description of the technique.")


class AutomotiveThreatReference(BaseModel):
    """
    Structured representation of Automotive Threat Matrix (ATM) entry.
    """

    atm_id: str = Field(..., description="Automotive Threat Matrix identifier.")
    category: str = Field(..., description="Threat category, e.g., 'Telematics remote exploit'.")
    description: str = Field(..., description="Summary description of the automotive threat.")
