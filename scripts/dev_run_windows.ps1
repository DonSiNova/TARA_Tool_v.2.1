Write-Host "`n[AutoTARA] Launching Streamlit UI on port 8501...`n"

# Move to project root (this script is in scripts/)
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location ..

$env:PYTHONPATH = (Get-Location).Path

streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AutoTARA][ERROR] Streamlit failed to start." -ForegroundColor Red
    exit 1
}
