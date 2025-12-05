# normalization.py
"""
Unified normalization module for AutoTARA.
This ensures all LLM outputs are mapped into valid enum/domain values
before they reach Pydantic models.

This avoids literal mismatch errors such as:
- "moderate" → should be "medium"
- "Medium-high" → should be "high" or "medium"
- "verylow" → should be "very low"
- "conf" → "confidentiality"
- "unauth access" → "access control"

Every stage MUST call:
normalized_value = normalize(field_name, raw_value)
before constructing Pydantic models.
"""

import re


# ---------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------

def _clean(value: str) -> str:
    """Basic cleanup: strip, lower-case, remove punctuation."""
    if not value:
        return ""
    v = value.strip().lower()
    v = re.sub(r"[^a-z0-9\s-]", "", v)
    v = v.replace("_", " ")
    return v


# ---------------------------------------------------------------------
# ATTACK FEASIBILITY
# Allowed: High, Medium, Low, Very Low
# ---------------------------------------------------------------------

def normalize_feasibility(value: str) -> str:
    v = _clean(value)

    if "very low" in v:
        return "Very Low"
    if "low" in v and "very" not in v:
        return "Low"
    if "medium" in v or "med" in v:
        return "Medium"
    if "high" in v:
        return "High"
    if "moderat" in v:
        return "Medium"
    if "mid" in v:
        return "Medium"

    return "Medium"  # safest fallback


# ---------------------------------------------------------------------
# ATTACK POTENTIAL
# Allowed: very low, low, medium, high
# ---------------------------------------------------------------------

def normalize_potential(value: str) -> str:
    v = _clean(value)

    if "very low" in v:
        return "very low"
    if "low" in v and "very" not in v:
        return "low"
    if "medium" in v or "med" in v:
        return "medium"
    if "high" in v:
        return "high"
    if "moderat" in v:
        return "medium"
    if "mid" in v:
        return "medium"

    return "medium"


# ---------------------------------------------------------------------
# CYBERSECURITY PROPERTIES
# Allowed: Confidentiality, Integrity, Availability, Authenticity, Authorization, Non-Repudiation
# ---------------------------------------------------------------------

CYBER_MAP = {
    "conf": "Confidentiality",
    "confidential": "Confidentiality",
    "confidentiality": "Confidentiality",

    "integ": "Integrity",
    "integrity": "Integrity",

    "avail": "Availability",
    "availability": "Availability",

    "authn": "Authenticity",
    "authenticity": "Authenticity",
    "authentic": "Authenticity",

    "authz": "Authorization",
    "authorization": "Authorization",
    "authorisation": "Authorization",

    "nonrep": "Non-Repudiation",
    "nonrepudiation": "Non-Repudiation",
    "non repudiation": "Non-Repudiation",
}

def normalize_cyber_property(value: str) -> str:
    v = _clean(value)
    for k, mapped in CYBER_MAP.items():
        if k in v:
            return mapped
    return "Integrity"  # neutral fallback


# ---------------------------------------------------------------------
# IMPACT / DAMAGE LEVELS
# Allowed: Very Low, Low, Medium, High, Very High
# ---------------------------------------------------------------------

def normalize_damage(value: str) -> str:
    v = _clean(value)

    if "very high" in v:
        return "Very High"
    if "high" in v and "very" not in v:
        return "High"
    if "medium" in v or "med" in v:
        return "Medium"
    if "very low" in v:
        return "Very Low"
    if "low" in v and "very" not in v:
        return "Low"
    if "critical" in v:
        return "High"
    if "severe" in v:
        return "High"
    if "moderate" in v:
        return "Medium"

    return "Medium"


# ---------------------------------------------------------------------
# LIKELIHOOD LEVELS
# Allowed: very low, low, medium, high
# ---------------------------------------------------------------------

def normalize_likelihood(value: str) -> str:
    v = _clean(value)

    if "very low" in v:
        return "very low"
    if "low" in v and "very" not in v:
        return "low"
    if "med" in v or "medium" in v:
        return "medium"
    if "high" in v:
        return "high"
    if "moderat" in v:
        return "medium"

    return "medium"


# ---------------------------------------------------------------------
# RISK VALUE
# Allowed: very low, low, medium, high
# ---------------------------------------------------------------------

def normalize_risk_value(value: str) -> str:
    return normalize_likelihood(value)


# ---------------------------------------------------------------------
# FALLBACK GENERIC NORMALIZER
# ---------------------------------------------------------------------

def normalize_generic(value: str) -> str:
    """Fallback for unknown categories."""
    if not value:
        return ""
    return value.strip()


# ---------------------------------------------------------------------
# MASTER DISPATCH FUNCTION
# ---------------------------------------------------------------------

def normalize(field: str, value: str) -> str:
    """
    Unified entry for normalization.

    Example:
        normalize("attackFeasibility", "Medium-high")
        normalize("attackPotential", "moderate")
        normalize("cyberProperty", "conf")
        normalize("damage", "critical")
    """
    f = field.lower()

    # Attack Feasibility
    if "feasib" in f:
        return normalize_feasibility(value)

    # Attack Potential
    if "potential" in f:
        return normalize_potential(value)

    # Cybersecurity Property
    if "cyber" in f or "property" in f:
        return normalize_cyber_property(value)

    # Damage / Impact
    if "damage" in f or "impact" in f:
        return normalize_damage(value)

    # Likelihood
    if "likelihood" in f:
        return normalize_likelihood(value)

    # Risk Value
    if "risk" in f and "value" in f:
        return normalize_risk_value(value)

    # Fallback
    return normalize_generic(value)
