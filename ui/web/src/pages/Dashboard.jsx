import React from "react";
import StageCard from "../components/StageCard";

export default function Dashboard() {
  return (
    <div className="p-10 grid grid-cols-1 md:grid-cols-3 gap-8">
      
      <StageCard
        title="Stage 1 — Asset Extraction"
        description="Parse SysML model and extract automotive cybersecurity assets."
        buttonText="Open"
        onClick={() => window.location.href = "/stage1"}
      />

      <StageCard
        title="Stage 2 — Damage Scenarios"
        description="Generate ISO 21434-compliant damage scenarios."
        buttonText="Open"
        onClick={() => window.location.href = "/stage2"}
      />

      <StageCard
        title="Stage 3 — Impact Rating"
        description="Derive SFOP/RFOIP impact scores."
        buttonText="Open"
        onClick={() => window.location.href = "/stage3"}
      />

      <StageCard
        title="Stage 4 — Threat Scenarios"
        description="Generate STRIDE-based threat scenarios."
        buttonText="Open"
        onClick={() => window.location.href = "/stage4"}
      />

      <StageCard
        title="Stage 5 — Attack Paths"
        description="Generate NVD-backed or potential attack paths."
        buttonText="Open"
        onClick={() => window.location.href = "/stage5"}
      />

      <StageCard
        title="Stage 6 — Attack Feasibility"
        description="Evaluate attacker effort and feasibility levels."
        buttonText="Open"
        onClick={() => window.location.href = "/stage6"}
      />

      <StageCard
        title="Stage 7 — Risk Matrix"
        description="Compute final risk values using risk matrix."
        buttonText="Open"
        onClick={() => window.location.href = "/stage7"}
      />

    </div>
  );
}
