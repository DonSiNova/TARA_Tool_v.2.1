// src/pages/Stage2.jsx
import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function Stage2() {
  const [loading, setLoading] = useState(false);
  const [csv, setCsv] = useState(null);
  const [stakeholder, setStakeholder] = useState("Road User");
  const [assets, setAssets] = useState([]);
  const [assetId, setAssetId] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await api.getAssets();
        const list = res.data || [];
        setAssets(list);
        if (list.length) {
          setAssetId(list[0].assetId);
          setError(null);
        } else {
          setError("Run Stage 1 to populate assets before generating damage scenarios.");
        }
      } catch (err) {
        console.error(err);
        setError("Unable to load assets. Run Stage 1 first.");
      }
    };

    fetchAssets();
  }, []);

  const runStage = async () => {
    try {
      if (!assetId) {
        setError("Select an asset before running Stage 2.");
        return;
      }
      setLoading(true);
      setError(null);

      await api.runStage(2, { stakeholder, assetId });

      const res = await api.getCsv("damage_scenarios.csv");
      setCsv(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to run Stage 2. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold text-primary">
        Stage 2 — Damage Scenarios
      </h1>

      <p className="mt-2 text-gray-700">
        Generate stakeholder-specific damage scenarios for each asset and
        cyber property, following ISO 21434.
      </p>

      <div className="mt-4 flex items-center gap-4">
        <span className="text-gray-700">Asset:</span>
        <select
          className="border rounded-lg px-3 py-2 bg-white flex-1"
          value={assetId}
          onChange={(e) => setAssetId(e.target.value)}
          disabled={!assets.length}
        >
          {assets.map((asset) => (
            <option key={asset.assetId} value={asset.assetId}>
              {asset.assetId} — {asset.description}
            </option>
          ))}
        </select>
      </div>

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
        disabled={loading || !assetId}
        className="mt-6 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent transition"
      >
        {loading ? "Running..." : "Run Stage 2"}
      </button>

      {error && (
        <div className="mt-4 text-red-600 font-semibold">{error}</div>
      )}

      {csv && (
        <>
          <h2 className="mt-8 text-xl font-semibold text-primary">
            damage_scenarios.csv
          </h2>
          <pre className="mt-3 bg-softgray p-4 rounded-xl overflow-auto max-h-[500px] text-sm">
            {csv}
          </pre>
        </>
      )}
    </div>
  );
}
