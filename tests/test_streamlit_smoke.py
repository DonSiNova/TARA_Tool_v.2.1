# tests/test_streamlit_smoke.py
def test_streamlit_importable():
    # This is just a smoke test to ensure the file parses.
    import ui.streamlit_app  # noqa: F401
