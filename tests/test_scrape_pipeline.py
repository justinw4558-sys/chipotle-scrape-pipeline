# tests/test_scrape_pipeline.py
import importlib
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Helper: import the helper function without running the script body
# ---------------------------------------------------------------------------
def _import_slug_helper():
    """Import only _url_to_slug from scrape_pipeline without executing it."""
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(
        "scrape_pipeline",
        Path(__file__).parent.parent / "scrape_pipeline.py",
    )
    # We need to prevent the script body from running; we do this by
    # patching load_dotenv, os.getenv, and requests.post before loading.
    with patch("dotenv.load_dotenv"), \
         patch("os.getenv", return_value="fake-key"), \
         patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"data": {"web": []}}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod._url_to_slug


# ---------------------------------------------------------------------------
# Slug tests
# ---------------------------------------------------------------------------
def test_slug_strips_https():
    slug = _import_slug_helper()
    assert slug("https://ir.chipotle.com/news-releases") == "ir_chipotle_com_news-releases"

def test_slug_strips_http():
    slug = _import_slug_helper()
    assert slug("http://newsroom.chipotle.com/press-releases") == "newsroom_chipotle_com_press-releases"

def test_slug_replaces_dots_and_slashes():
    slug = _import_slug_helper()
    assert slug("https://ir.chipotle.com/") == "ir_chipotle_com_"

# ---------------------------------------------------------------------------
# File writing tests
# ---------------------------------------------------------------------------
def _run_pipeline(tmp_path, results):
    """Run scrape_pipeline.py with mocked results, writing to tmp_path."""
    fake_response = MagicMock()
    fake_response.json.return_value = {"data": {"web": results}}

    import os
    import importlib.util

    orig = os.getcwd()
    orig_path = Path(orig) / "scrape_pipeline.py"

    with patch("dotenv.load_dotenv"), \
         patch("os.getenv", return_value="fake-key"), \
         patch("requests.post", return_value=fake_response):
        # We can't easily redirect Path("knowledge/raw") to tmp_path via
        # patching Path, so we use a simpler approach: chdir to tmp_path.
        os.chdir(tmp_path)
        try:
            spec = importlib.util.spec_from_file_location(
                "scrape_pipeline_run",
                str(orig_path),
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module spec from {orig_path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            os.chdir(orig)


def test_output_dir_created(tmp_path):
    _run_pipeline(tmp_path, [])
    assert (tmp_path / "knowledge" / "raw").is_dir()


def test_file_created_for_each_result(tmp_path):
    results = [
        {"title": "News", "url": "https://ir.chipotle.com/news", "markdown": "# News"},
        {"title": "SEC", "url": "https://ir.chipotle.com/sec", "markdown": "# SEC"},
    ]
    _run_pipeline(tmp_path, results)
    files = list((tmp_path / "knowledge" / "raw").glob("*.md"))
    assert len(files) == 2


def test_file_has_frontmatter(tmp_path):
    results = [
        {"title": "News Releases", "url": "https://ir.chipotle.com/news", "markdown": "# Body"},
    ]
    _run_pipeline(tmp_path, results)
    files = list((tmp_path / "knowledge" / "raw").glob("*.md"))
    content = files[0].read_text()
    assert content.startswith("---\n")
    assert "title: News Releases" in content
    assert "url: https://ir.chipotle.com/news" in content
    assert "# Body" in content


def test_empty_markdown_still_writes_file(tmp_path):
    results = [
        {"title": "Empty", "url": "https://ir.chipotle.com/empty", "markdown": None},
    ]
    _run_pipeline(tmp_path, results)
    files = list((tmp_path / "knowledge" / "raw").glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "title: Empty" in content
