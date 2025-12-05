import React, { useState } from "react";
import { api } from "../api";
import FileUpload from "../components/FileUpload";

export default function Stage1() {
  const [loading, setLoading] = useState(false);
  const [csv, setCsv] = useState(null);

  const handleUpload = async (file) => {
    const fd = new FormData();
    fd.append("file", file);

    setLoading(true);
    await api.uploadSysML(fd);
    setLoading(false);
  };

  const runStage = async () => {
    setLoading(true);
    await api.runStage(1);
    const res = await api.getCsv("assets.csv");
    setCsv(res.data);
    setLoading(false);
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold text-primary">Stage 1 — Asset Extraction</h1>

      <p className="mt-2 text-gray-700">
        Upload your SysML model and extract all automotive cybersecurity assets.
      </p>

      <div className="mt-6">
        <FileUpload onUpload={handleUpload} />
      </div>

      <button
        onClick={runStage}
        className="mt-6 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent"
      >
        {loading ? "Running..." : "Run Stage 1"}
      </button>

      {csv && (
        <pre className="mt-6 bg-softgray p-4 rounded-xl">{csv}</pre>
      )}
    </div>
  );
}
