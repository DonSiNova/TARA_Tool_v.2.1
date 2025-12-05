// src/pages/Stage5.jsx
import React, { useState } from "react";
import { api } from "../api";

export default function Stage5() {
  const [loading, setLoading] = useState(false);
  const [csv, setCsv] = useState(null);
  const [error, setError] = useState(null);

  const runStage = async () => {
    try {
      setLoading(true);
      setError(null);

      await api.runStage(5);

      const res = await api.getCsv("attack_paths.csv");
      setCsv(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to run Stage 5. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold text-primary">
        Stage 5 — Vulnerabilities & Attack Paths
      </h1>

      <p className="mt-2 text-gray-700">
        Enrich threats with NVD-backed vulnerabilities and potential attack
        paths, including CWE, CAPEC, ATT&CK and ATM mappings.
      </p>

      <button
        onClick={runStage}
        disabled={loading}
        className="mt-6 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent transition"
      >
        {loading ? "Running..." : "Run Stage 5"}
      </button>

      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
      )}

      {csv && (
        <>
          <h2 className="mt-8 text-xl font-semibold text-primary">
            attack_paths.csv
          </h2>
          <pre className="mt-3 bg-softgray p-4 rounded-xl overflow-auto max-h-[500px] text-sm">
            {csv}
          </pre>
        </>
      )}
    </div>
  );
}
