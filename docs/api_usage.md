# AutoTARA-RAG API Usage Guide

This document describes how to interact with the FastAPI backend.

Base URL (local dev):

- `http://localhost:8000`

---

## 1. Upload SysML

**Endpoint**

- `POST /upload-sysml`
- Body: `multipart/form-data` with field `"file"` (JSON SysML model)

**Example**

```bash
curl -X POST http://localhost:8000/upload-sysml \
  -F "file=@sysmodel.json"
