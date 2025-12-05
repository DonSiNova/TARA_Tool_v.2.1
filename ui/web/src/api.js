// src/api.js
import axios from "axios";

const API_BASE = "http://localhost:8000";

export const api = {
  uploadSysML: (formData) =>
    axios.post(`${API_BASE}/upload-sysml`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  // Optional body supported (e.g. { stakeholder: "Road User" })
  runStage: (id, data = {}) =>
    axios.post(`${API_BASE}/run-stage/${id}`, data),

  getAssets: () => axios.get(`${API_BASE}/assets`),

  getCsv: (name) => axios.get(`${API_BASE}/csv/${name}`),

  regenerate: (stage, payload) =>
    axios.post(`${API_BASE}/modify/${stage}`, payload),
};
