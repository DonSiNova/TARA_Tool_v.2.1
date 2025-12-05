@echo off
REM ==========================================================
REM AutoTARA-RAG — Windows Development Launcher
REM Local-only, no cloud deployment logic.
REM ==========================================================

SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo [AutoTARA] Starting Streamlit UI on port 8501...
echo.

REM Ensure current directory is project root
cd /d "%~dp0.."

REM Set PYTHONPATH so imports work
set PYTHONPATH=%cd%

streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
IF %ERRORLEVEL% NEQ 0 (
    echo [AutoTARA][ERROR] Streamlit failed to start.
    pause
    exit /b 1
)

ENDLOCAL
