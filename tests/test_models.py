# tests/test_models.py
from models.schemas import (
    Asset,
    Interface,
    SoftwareComponent,
    DamageScenario,
    ImpactRating,
    ThreatScenario,
    AttackPath,
    VulnerabilityRef,
    AttackFeasibility,
    RiskValue,
)


def test_asset_minimal():
    asset = Asset(
        assetId="A1",
        itemId="ITEM1",
        type="ECU",
        description="ABS ECU",
        location="Engine bay",
        cyberProperties=["Confidentiality", "Integrity"],
        interfaces=[Interface(type="CAN", direction="inout", exposure="vehicle-internal")],
        softwareStack=[
            SoftwareComponent(
                name="RTOS",
                version="1.0.0",
                vendor="VendorX",
                category="OS",
            )
        ],
    )
    assert asset.assetId == "A1"
    assert asset.type == "ECU"
    assert len(asset.cyberProperties) == 2


def test_damage_scenario():
    ds = DamageScenario(
        damageId="D1",
        assetId="A1",
        cyber_property="Integrity",
        one_sentence="!!!!Loss of integrity leads to unintended braking!!!!",
        raw_llm_output="some text",
        stakeholder="Road User",
    )
    assert ds.damageId == "D1"
    assert ds.stakeholder == "Road User"


def test_impact_rating():
    ir = ImpactRating(
        impactId="I1",
        damageId="D1",
        stakeholder="Road User",
        road_user_sfop={"safety": 3, "financial": 1, "operational": 2, "privacy": 0},
        oem_rfoip=None,
        raw_llm_output="raw text",
    )
    assert ir.road_user_sfop["safety"] == 3


def test_threat_scenario():
    ts = ThreatScenario(
        threatId="T1",
        damageId="D1",
        assetId="A1",
        cyber_property="Integrity",
        one_sentence="ECU firmware is tampered over CAN",
        attack_vectors=["Network"],
        raw_llm_output="raw",
    )
    assert "Network" in ts.attack_vectors


def test_attack_path_and_vuln_ref():
    vref = VulnerabilityRef(
        backing="NVD",
        cve_id="CVE-2023-0001",
        cwe_id="CWE-79",
        component="RTOS",
        cpe_candidates=[{"cpe": "cpe:/a:vendor:rtos:1.0", "confidence": "HIGH"}],
        weakness_family="memory_corruption",
        attack_vectors=["Network"],
    )
    ap = AttackPath(
        pathId="P1",
        threatId="T1",
        assetId="A1",
        damageId="D1",
        vulnerabilities=[vref],
        entry_vector="Network",
        backing="NVD-supported",
        cve_id="CVE-2023-0001",
        cwe_id="CWE-79",
        attck_techniques=["T1059.003"],
        capec_ids=["CAPEC-123"],
        atm_ids=["ATM-001"],
        steps=["Step 1", "Step 2"],
        raw_llm_output="raw",
    )
    assert ap.vulnerabilities[0].cve_id == "CVE-2023-0001"


def test_attack_feasibility_and_risk():
    feas = AttackFeasibility(
        feasibilityId="F1",
        threatId="T1",
        pathId="P1",
        mappedCVE=["CVE-2023-0001"],
        cwe=["CWE-79"],
        elapsedTime_score=2,
        specialistExpertise_score=1,
        knowledgeOfItem_score=1,
        windowOfOpportunity_score=1,
        equipmentRequired_score=1,
        totalScore=6,
        attackPotential="Moderate",
        attackFeasibility="Medium",
        raw_llm_output="raw",
    )
    assert feas.totalScore == 6

    rv = RiskValue(
        riskId="R1",
        threatId="T1",
        stakeholder="Road User",
        impactCategory="severe",
        attackPotential="high",
        riskValue=5,
        justification="High impact and relatively low attacker cost.",
    )
    assert rv.riskValue == 5
