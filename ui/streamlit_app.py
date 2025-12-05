# ui/streamlit_app.py
"""
Streamlit UI for AutoTARA-RAG with a modern hero section and tabbed workflow.
"""

import os
import base64
from pathlib import Path
import sys

import streamlit as st

# Ensure project root on path for `app.*` imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.orchestrator import TARAOrchestrator
from config.settings import settings
from config.logging import configure_logging
from models.schemas import Asset
from storage.csv_store import (
    get_assets_csv_path,
    get_damage_csv_path,
    get_impact_csv_path,
    get_threat_csv_path,
    get_attack_paths_csv_path,
    get_attack_feasibilities_csv_path,
    get_risk_values_csv_path,
)
from storage.run_state import get_run_dir, start_new_run
from services.asset_utils import load_assets

st.set_page_config(
    page_title="AutoTARA-RAG",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
HERO_IMAGE_PATH = APP_DIR / "assets" / "autotara_hero.png"
HERO_IMAGE_WIDTH = 350


if "active_stage_index" not in st.session_state:
    st.session_state["active_stage_index"] = 0


STAGE_LABELS = [
    "Stage 1 - Assets",
    "Stage 2 - Damage",
    "Stage 3 - Impact",
    "Stage 4 - Threats",
    "Stage 5 - Attack Paths",
    "Stage 6 - Feasibility",
    "Stage 7 - Risk Matrix",
]


def _inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 10% 20%, #0b1f24 0%, #03060f 65%);
            color: #e5ebff;
            font-family: "Inter", "Segoe UI", sans-serif;
            padding-bottom: 3rem;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent;
        }
        [data-testid="stSidebar"] {
            background: #050912;
        }
        .autotara-hero {
            text-align: center;
            padding-top: 0.5rem;
        }
        .autotara-hero h1 {
            font-size: 3rem;
            margin-bottom: 0.3rem;
            color: #f6f8ff;
        }
        .autotara-hero p {
            color: #b4c4e4;
            font-size: 1.1rem;
            margin-bottom: 0;
        }
        .hero-kicker {
            font-weight: 600;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #8dc0ff;
            font-size: 0.9rem;
            margin-bottom: 0.4rem;
        }
        .cta-pill {
            display: inline-block;
            margin: 0.6rem 0.4rem 0;
            padding: 0.35rem 0.95rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.05);
            color: #d4e0ff;
            font-size: 0.95rem;
        }
        .autotara-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0 2rem;
        }
        .autotara-card {
            background: rgba(7, 14, 28, 0.88);
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1.2rem 1.4rem;
            box-shadow: 0 25px 60px rgba(3, 7, 18, 0.6);
            backdrop-filter: blur(12px);
        }
        .autotara-card h3 {
            margin: 0;
            font-size: 0.9rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #86b9ff;
        }
        .autotara-card p {
            margin: 0.4rem 0 0;
            font-size: 1.25rem;
            color: #f5f8ff;
            font-weight: 600;
        }
        .hero-image-container {
            display: flex;
            justify-content: center;
            padding-top: 0.5rem;
            margin-bottom: 0.4rem;
        }
        .accent-text, .accent-text * {
            color: #86b9ff !important;
        }
        .stage-feedback {
            margin: 1rem 0;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            color: #5a6a8f;
            font-weight: 600;
            border-bottom: 2px solid transparent;
            padding-bottom: 0.4rem;
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #ff6d6d;
            border-bottom: 2px solid #ff6d6d;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_hero_image_base64() -> str | None:
    if HERO_IMAGE_PATH.exists():
        encoded = base64.b64encode(HERO_IMAGE_PATH.read_bytes()).decode("utf-8")
        return encoded
    return None


def _complete_stage(
    message: str,
    next_stage_index: int,
) -> None:
    st.session_state["stage_feedback"] = message
    st.session_state["active_stage_index"] = min(next_stage_index, len(STAGE_LABELS) - 1)


def _accent_block(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="accent-text">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_csv(path: str, label: str) -> None:
    if not os.path.exists(path):
        st.warning(f"{label}: CSV does not exist yet.")
        return

    import pandas as pd

    df = pd.read_csv(path)
    st.subheader(label)
    st.dataframe(df, use_container_width=True)


def _load_assets_from_csv() -> list[Asset]:
    try:
        return load_assets()
    except Exception:
        return []


def _asset_selector(key: str, show_warning: bool = True) -> str | None:
    assets = _load_assets_from_csv()
    if not assets:
        if show_warning:
            st.warning("Run Stage 1 to extract assets before proceeding.")
        return None

    options = {
        f"{a.assetTag or 'N/A'} | {a.assetId} - {a.description}": a.assetId
        for a in assets
    }
    option_labels = list(options.keys())
    default_asset = st.session_state.get("selected_asset")
    default_label = next(
        (label for label, a_id in options.items() if a_id == default_asset), None
    )
    default_index = option_labels.index(default_label) if default_label in option_labels else 0
    selected_label = st.selectbox(
        "Select asset",
        options=option_labels,
        index=default_index,
        key=key,
        label_visibility="collapsed",
    )
    selected_asset = options[selected_label]
    st.session_state["selected_asset"] = selected_asset
    return selected_asset


def _set_active_asset(asset_id: str) -> None:
    st.session_state["selected_asset"] = asset_id


def _get_active_asset() -> str | None:
    return st.session_state.get("selected_asset")


def _get_asset_label(asset_id: str | None) -> str | None:
    if not asset_id:
        return None
    assets = _load_assets_from_csv()
    for asset in assets:
        if asset.assetId == asset_id or asset.assetTag == asset_id:
            return f"{asset.assetTag or 'N/A'} | {asset.assetId} - {asset.description}"
    return asset_id


def _reset_workflow() -> None:
    """
    Clear Streamlit session state and start a new timestamped run directory.
    """
    start_new_run()
    sysml_path = os.path.join(settings.OUTPUT_DIR, "uploaded_sysml.json")
    if os.path.exists(sysml_path):
        os.remove(sysml_path)

    st.session_state.clear()
    st.session_state["active_stage_index"] = 0
    st.session_state["stage1_completed"] = False
    st.session_state["reuse_run_dir"] = True
    st.experimental_rerun()


def _render_active_asset_summary() -> None:
    st.markdown('<div class="accent-text" style="text-align:left;">Active Asset</div>', unsafe_allow_html=True)
    header_asset_label = _get_asset_label(st.session_state.get("selected_asset"))
    st.warning("Run Stage 1 to extract assets before proceeding.")
    st.info(header_asset_label or "No Asset Selected")


def _render_main_content(sysml_path: str | None) -> None:
    stage_tabs = st.tabs(STAGE_LABELS)

    with stage_tabs[0]:
        _accent_block(
            "Stage 1 - Initial Analysis / Asset Extraction",
            "Translate SysML structures into an actionable asset inventory before RAG enrichment.",
        )
        selected_asset = _asset_selector("global_asset", show_warning=False)
        stage1_completed = st.session_state.get("stage1_completed", False)
        run_clicked = st.button(
            "Run Stage 1",
            key="run_stage_1",
            disabled=stage1_completed,
        )

        if run_clicked:
            if not sysml_path:
                st.error("Upload a SysML file first.")
            else:
                reuse_run_dir = st.session_state.pop("reuse_run_dir", False)
                with st.spinner("Running Stage 1: Asset Extraction..."):
                    out = orchestrator.run_stage_1(sysml_path, force_new_run=not reuse_run_dir)
                st.session_state["stage1_status_msg"] = f"Stage 1 complete. {len(out)} assets extracted."
                if out:
                    _set_active_asset(out[0].assetId)
                st.session_state["stage1_completed"] = True
                st.session_state["active_stage_index"] = 1
                st.rerun()
        stage1_status = st.session_state.pop("stage1_status_msg", None)
        if stage1_status:
            st.success(stage1_status)
        elif stage1_completed:
            st.info("Reset the workflow to run Stage 1 again.")

    with stage_tabs[1]:
        _accent_block(
            "Stage 2 - Damage Scenarios",
            "Generate stakeholder-specific damage narratives aligned with Annex E guidance.",
        )
        asset_choice = _get_active_asset()
        asset_label = _get_asset_label(asset_choice)
        if asset_label:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        st.caption("Damage scenarios run for Road User by default.")
        if st.button("Generate Damage Scenarios", key="run_stage_2"):
            if not asset_choice:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 2 for asset {asset_label or asset_choice}...")
                out = orchestrator.run_stage_2(asset_choice)
                st.success(
                    f"Stage 2 complete. {len(out)} damage scenarios generated for {asset_label or asset_choice}."
                )
                st.session_state["selected_asset"] = asset_choice
                st.session_state["active_stage_index"] = 2
                display_csv(get_damage_csv_path(), "Damage Scenarios")

    with stage_tabs[2]:
        _accent_block(
            "Stage 3 - Impact Rating",
            "Score SFOP/RFOIP impacts with clear justification text for audit.",
        )
        asset_choice_3 = _get_active_asset()
        asset_label_3 = _get_asset_label(asset_choice_3)
        if asset_label_3:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label_3} (Road User + OEM)</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        if st.button("Generate Impact Ratings", key="run_stage_3"):
            if not asset_choice_3:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 3 for asset {asset_label_3 or asset_choice_3} (both stakeholders)...")
                out = orchestrator.run_stage_3(asset_choice_3)
                st.success(
                    f"Stage 3 complete. {len(out)} impact ratings generated for {asset_label_3 or asset_choice_3}."
                )
                st.session_state["selected_asset"] = asset_choice_3
                st.session_state["active_stage_index"] = 3
                display_csv(get_impact_csv_path(), "Impact Ratings")

    with stage_tabs[3]:
        _accent_block(
            "Stage 4 - Threat Scenarios",
            "Combine attack knowledge with system context to derive concrete threat scenarios.",
        )
        asset_choice_4 = _get_active_asset()
        asset_label_4 = _get_asset_label(asset_choice_4)
        if asset_label_4:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label_4}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        if st.button("Generate Threat Scenarios", key="run_stage_4"):
            if not asset_choice_4:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 4 for asset {asset_label_4 or asset_choice_4}...")
                out = orchestrator.run_stage_4(asset_choice_4)
                st.success(
                    f"Stage 4 complete. {len(out)} threat scenarios generated for {asset_label_4 or asset_choice_4}."
                )
                st.session_state["selected_asset"] = asset_choice_4
                st.session_state["active_stage_index"] = 4
                display_csv(get_threat_csv_path(), "Threat Scenarios")

    with stage_tabs[4]:
        _accent_block(
            "Stage 5 - Vulnerability & Attack Paths",
            "Map realistic attack paths with references to CVE/CWE/CAPEC artifacts for traceable mitigations.",
        )
        asset_choice_5 = _get_active_asset()
        asset_label_5 = _get_asset_label(asset_choice_5)
        if asset_label_5:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label_5}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        if st.button("Generate Attack Paths", key="run_stage_5"):
            if not asset_choice_5:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 5 for asset {asset_label_5 or asset_choice_5}...")
                out = orchestrator.run_stage_5(asset_choice_5)
                st.success(
                    f"Stage 5 complete. {len(out)} attack paths generated for {asset_label_5 or asset_choice_5}."
                )
                st.session_state["selected_asset"] = asset_choice_5
                st.session_state["active_stage_index"] = 5
                display_csv(get_attack_paths_csv_path(), "Attack Paths")

    with stage_tabs[5]:
        _accent_block(
            "Stage 6 - Attack Feasibility",
            "Quantify attacker effort using ET/SE/KOI/WOO/EQ scoring derived from feasibility prompts.",
        )
        asset_choice_6 = _get_active_asset()
        asset_label_6 = _get_asset_label(asset_choice_6)
        if asset_label_6:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label_6}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        if st.button("Generate Attack Feasibility", key="run_stage_6"):
            if not asset_choice_6:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 6 for asset {asset_label_6 or asset_choice_6}...")
                out = orchestrator.run_stage_6(asset_choice_6)
                st.success(
                    f"Stage 6 complete. {len(out)} feasibility scores generated for {asset_label_6 or asset_choice_6}."
                )
                st.session_state["selected_asset"] = asset_choice_6
                st.session_state["active_stage_index"] = 6
                display_csv(get_attack_feasibilities_csv_path(), "Attack Feasibilities")

    with stage_tabs[6]:
        _accent_block(
            "Stage 7 - Risk Matrix",
            "Convert feasibility plus impact categories into final risk values using the ISO/SAE matrix.",
        )
        asset_choice_7 = _get_active_asset()
        asset_label_7 = _get_asset_label(asset_choice_7)
        if asset_label_7:
            st.markdown(
                f"<div class='accent-text'>Active Asset: {asset_label_7}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Select an asset under Stage 1 before running this stage.")
        st.caption("Risk values run for Road User by default.")
        if st.button("Generate Risk Values", key="run_stage_7"):
            if not asset_choice_7:
                st.error("Select an asset first.")
            else:
                st.info(f"Running Stage 7 for asset {asset_label_7 or asset_choice_7}...")
                out = orchestrator.run_stage_7(asset_choice_7)
                st.success(
                    f"Stage 7 complete. {len(out)} risk values generated for {asset_label_7 or asset_choice_7}."
                )
                st.session_state["selected_asset"] = asset_choice_7
                st.session_state["active_stage_index"] = 6
                display_csv(get_risk_values_csv_path(), "Risk Values")

    st.markdown(
        """
        <div class="accent-text">
            <h3>Output repository</h3>
            <p>Every stage deposits CSV evidence in the configured output directory for downstream consumption.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Show Output Files", key="show_outputs"):
        base_dir = settings.OUTPUT_DIR
        st.markdown(f"**{base_dir}**")
        if not os.path.exists(base_dir):
            st.info("No output files generated yet.")
        else:
            entries = sorted(os.listdir(base_dir), reverse=True)
            if not entries:
                st.info("No output files generated yet.")
            for entry in entries:
                path = os.path.join(base_dir, entry)
                if os.path.isdir(path):
                    file_count = sum(len(files) for _, _, files in os.walk(path))
                    st.markdown(f"- **{entry}/** ({file_count} files)")
                else:
                    st.markdown(f"- {entry} - {os.path.getsize(path)} bytes")


_inject_global_styles()

orchestrator = TARAOrchestrator()
logger = configure_logging(get_run_dir())

hero_image_b64 = _load_hero_image_base64()
if hero_image_b64:
    st.markdown(
        f"""
        <div class="hero-image-container">
            <img src="data:image/png;base64,{hero_image_b64}" width="{HERO_IMAGE_WIDTH}" alt="AutoTARA" />
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    placeholder_path = HERO_IMAGE_PATH.relative_to(Path.cwd())
    st.info(
        f"Place the provided hero image at '{placeholder_path}' to display it here."
    )

st.markdown(
    """
    <div class="autotara-hero">
        <div class="hero-kicker">Automotive Cybersecurity Intelligence</div>
        <h1>AutoTara Mission Console</h1>
        <p>Evidence-backed ISO/SAE 21434 workflow combining SysML context, RAG knowledge, and guided approvals.</p>
        <div>
            <span class="cta-pill">Model-based automation</span>
            <span class="cta-pill">LLM + RAG orchestration</span>
            <span class="cta-pill">Audit-ready CSV outputs</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="autotara-metrics">
        <div class="autotara-card">
            <h3>Standards Coverage</h3>
            <p>ISO/SAE 21434 + UNECE R155</p>
        </div>
        <div class="autotara-card">
            <h3>Threat Knowledge</h3>
            <p>CVEs - CWE - CAPEC - ATT&CK</p>
        </div>
        <div class="autotara-card">
            <h3>Automation Depth</h3>
            <p>7 sequenced stages</p>
        </div>
        <div class="autotara-card">
            <h3>Evidence Trail</h3>
            <p>CSV + narrative logs</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


content_col, sidebar_col = st.columns([2.3, 1], gap="large")

with content_col:
    _accent_block(
        "Upload SysML baseline",
        "Provide the SysML JSON export so AutoTARA can anchor every downstream stage.",
    )
    st.markdown('<div class="accent-text">Upload SysML Model (.json)</div>', unsafe_allow_html=True)
    upload_left, upload_right = st.columns([1, 1])
    with upload_left:
        uploaded = st.file_uploader(
            "Upload SysML Model (.json)",
            type=["json"],
            key="sysml_upload",
            label_visibility="collapsed",
        )
    if uploaded:
        sysml_path = os.path.join(settings.OUTPUT_DIR, "uploaded_sysml.json")
        with open(sysml_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Uploaded SysML to: {sysml_path}")
    else:
        sysml_path = None

    _accent_block(
        "Operational workflow",
        "Execute stages individually or sequentially; each tab surfaces the relevant action and evidence preview.",
    )
    _render_main_content(sysml_path)

with sidebar_col:
    _render_active_asset_summary()
    display_csv(get_assets_csv_path(), "Assets")

reset_col, _ = st.columns([1, 5])
with reset_col:
    if st.button("🔄 Reset Workflow", key="reset_workflow_global"):
        _reset_workflow()

st.markdown(
    """
    <div class="accent-text">
        AutoTARA - Continuous TARA intelligence for software-defined vehicles.
    </div>
    """,
    unsafe_allow_html=True,
 )
