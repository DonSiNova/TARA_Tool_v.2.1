import React from "react";

export default function StageCard({ title, description, buttonText, onClick, loading }) {
  return (
    <div className="bg-white shadow-lg rounded-2xl p-6 border border-gray-100 hover:shadow-xl transition">
      <h2 className="text-xl font-bold text-primary">{title}</h2>
      <p className="text-gray-600 mt-2">{description}</p>

      <button
        onClick={onClick}
        disabled={loading}
        className="mt-4 bg-primary text-white px-4 py-2 rounded-lg hover:bg-accent transition"
      >
        {loading ? "Running..." : buttonText}
      </button>
    </div>
  );
}
