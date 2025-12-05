@echo off
echo [+] Starting AutoTARA Backend on port 8000...
set PYTHONPATH=%cd%
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
