// src/pages/Stage3.jsx
import React, { useState } from "react";
import { api } from "../api";

export default function Stage3() {
  const [loading, setLoading] = useState(false);
  const [csv, setCsv] = useState(null);
  const [error, setError] = useState(null);

  const runStage = async () => {
    try {
      setLoading(true);
      setError(null);

      await api.runStage(3);

      const res = await api.getCsv("impact_rating.csv");
      setCsv(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to run Stage 3. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold text-primary">
        Stage 3 — Impact Rating
      </h1>

      <p className="mt-2 text-gray-700">
        Derive SFOP / RFOIP impact scores for each damage scenario and
        stakeholder.
      </p>

      <button
        onClick={runStage}
        disabled={loading}
        className="mt-6 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent transition"
      >
        {loading ? "Running..." : "Run Stage 3"}
      </button>

      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
      )}

      {csv && (
        <>
          <h2 className="mt-8 text-xl font-semibold text-primary">
            impact_rating.csv
          </h2>
          <pre className="mt-3 bg-softgray p-4 rounded-xl overflow-auto max-h-[500px] text-sm">
            {csv}
          </pre>
        </>
      )}
    </div>
  );
}
