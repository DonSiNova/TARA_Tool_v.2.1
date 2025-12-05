// src/pages/Stage7.jsx
import React, { useState } from "react";
import { api } from "../api";

export default function Stage7() {
  const [loading, setLoading] = useState(false);
  const [csv, setCsv] = useState(null);
  const [stakeholder, setStakeholder] = useState("Road User");
  const [error, setError] = useState(null);

  const runStage = async () => {
    try {
      setLoading(true);
      setError(null);

      await api.runStage(7, { stakeholder });

      const res = await api.getCsv("risk_values.csv");
      setCsv(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to run Stage 7. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold text-primary">
        Stage 7 — Risk Matrix & Final Risk Values
      </h1>

      <p className="mt-2 text-gray-700">
        Combine impact ratings and attack feasibility to derive final risk
        values per threat and stakeholder using the risk matrix.
      </p>

      <div className="mt-4 flex items-center gap-4">
        <span className="text-gray-700">Stakeholder:</span>
        <select
          className="border rounded-lg px-3 py-2 bg-white"
          value={stakeholder}
          onChange={(e) => setStakeholder(e.target.value)}
        >
          <option>Road User</option>
          <option>OEM</option>
        </select>
      </div>

      <button
        onClick={runStage}
        disabled={loading}
        className="mt-6 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent transition"
      >
        {loading ? "Running..." : "Run Stage 7"}
      </button>

      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
      )}

      {csv && (
        <>
          <h2 className="mt-8 text-xl font-semibold text-primary">
            risk_values.csv
          </h2>
          <pre className="mt-3 bg-softgray p-4 rounded-xl overflow-auto max-h-[500px] text-sm">
            {csv}
          </pre>
        </>
      )}
    </div>
  );
}
