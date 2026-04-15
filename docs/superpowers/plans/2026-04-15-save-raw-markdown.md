# Save Raw Markdown Files Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `scrape_pipeline.py` to save each Firecrawl result as a dated markdown file with YAML front-matter in `knowledge/raw/`.

**Architecture:** All changes are inline in `scrape_pipeline.py`. A small pure helper `_url_to_slug(url)` is extracted solely for testability. The loop gains three lines: build filename, build content string, write file.

**Tech Stack:** Python 3.12, pathlib, datetime, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `scrape_pipeline.py` | Modify | Add import, helper, directory setup, file writing |
| `tests/test_scrape_pipeline.py` | Create | Unit tests for slug helper and file writing behavior |

---

### Task 1: Write failing tests

**Files:**
- Create: `tests/test_scrape_pipeline.py`

- [ ] **Step 1: Create the test file**

```python
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

    with patch("dotenv.load_dotenv"), \
         patch("os.getenv", return_value="fake-key"), \
         patch("requests.post", return_value=fake_response), \
         patch("pathlib.Path.__new__") as _:
        # We can't easily redirect Path("knowledge/raw") to tmp_path via
        # patching Path, so we use a simpler approach: chdir to tmp_path.
        import os
        orig = os.getcwd()
        os.chdir(tmp_path)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scrape_pipeline_run",
                Path(orig) / "scrape_pipeline.py",
            )
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/pytest tests/test_scrape_pipeline.py -v
```

Expected: failures including `AttributeError: module 'scrape_pipeline' has no attribute '_url_to_slug'`

---

### Task 2: Add `datetime` import and `_url_to_slug` helper to `scrape_pipeline.py`

**Files:**
- Modify: `scrape_pipeline.py:1-6`

- [ ] **Step 1: Add `datetime` to imports**

Replace the import block at the top of `scrape_pipeline.py`:

```python
import os
import re
import time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import requests
```

- [ ] **Step 2: Add `_url_to_slug` helper after the imports block, before `load_dotenv()`**

```python
def _url_to_slug(url: str) -> str:
    """Convert a URL to a filesystem-safe slug (strip scheme, replace . and / with _)."""
    slug = re.sub(r"^https?://", "", url)
    slug = slug.replace(".", "_").replace("/", "_")
    return slug
```

- [ ] **Step 3: Run the slug tests only**

```bash
.venv/bin/pytest tests/test_scrape_pipeline.py -v -k "slug"
```

Expected: 3 slug tests PASS, file-writing tests still FAIL

---

### Task 3: Add directory setup and file writing to `scrape_pipeline.py`

**Files:**
- Modify: `scrape_pipeline.py` (the section after `results = ...` and the `for` loop)

- [ ] **Step 1: Add `out_dir` setup and `today` before the loop**

After the line `print(f"Firecrawl returned {len(results)} results")`, add:

```python
today = date.today().isoformat()
out_dir = Path("knowledge/raw")
out_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 2: Add file writing inside the loop**

After the three existing `print` lines inside `for r in results:`, add:

```python
    slug = _url_to_slug(r["url"])
    filename = f"{today}_{slug}.md"
    markdown_body = r.get("markdown") or ""
    content = (
        f"---\n"
        f"title: {r['title']}\n"
        f"url: {r['url']}\n"
        f"date: {today}\n"
        f"---\n\n"
        f"{markdown_body}"
    )
    (out_dir / filename).write_text(content, encoding="utf-8")
    print(f"    saved → {out_dir / filename}")
```

- [ ] **Step 3: Verify the full file looks correct**

`scrape_pipeline.py` should now look like this in full:

```python
import os
import re
import time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import requests


def _url_to_slug(url: str) -> str:
    """Convert a URL to a filesystem-safe slug (strip scheme, replace . and / with _)."""
    slug = re.sub(r"^https?://", "", url)
    slug = slug.replace(".", "_").replace("/", "_")
    return slug


load_dotenv()

api_key = os.getenv("FIRECRAWL_API_KEY")

# --- Step 01: Search + scrape with Firecrawl ---

api_url = "https://api.firecrawl.dev/v2/search"

headers = {
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "query": "Chipotle investor relations press releases",
    "limit": 5,
    "scrapeOptions": {"formats": ["markdown"]}
}

response = requests.post(api_url, headers=headers, json=payload)

data = response.json()
results = data["data"]["web"]
print(f"Firecrawl returned {len(results)} results")

today = date.today().isoformat()
out_dir = Path("knowledge/raw")
out_dir.mkdir(parents=True, exist_ok=True)

for r in results:
    print(f"  - {r['title']}")
    print(f"    {r['url']}")
    print(f"    markdown length: {len(r.get('markdown') or '')} chars")
    slug = _url_to_slug(r["url"])
    filename = f"{today}_{slug}.md"
    markdown_body = r.get("markdown") or ""
    content = (
        f"---\n"
        f"title: {r['title']}\n"
        f"url: {r['url']}\n"
        f"date: {today}\n"
        f"---\n\n"
        f"{markdown_body}"
    )
    (out_dir / filename).write_text(content, encoding="utf-8")
    print(f"    saved → {out_dir / filename}")
```

---

### Task 4: Run all tests and verify

**Files:** none

- [ ] **Step 1: Run the full test suite**

```bash
.venv/bin/pytest tests/test_scrape_pipeline.py -v
```

Expected output (all 8 tests):
```
PASSED tests/test_scrape_pipeline.py::test_slug_strips_https
PASSED tests/test_scrape_pipeline.py::test_slug_strips_http
PASSED tests/test_scrape_pipeline.py::test_slug_replaces_dots_and_slashes
PASSED tests/test_scrape_pipeline.py::test_output_dir_created
PASSED tests/test_scrape_pipeline.py::test_file_created_for_each_result
PASSED tests/test_scrape_pipeline.py::test_file_has_frontmatter
PASSED tests/test_scrape_pipeline.py::test_empty_markdown_still_writes_file
```

- [ ] **Step 2: Do a live smoke test**

```bash
.venv/bin/python scrape_pipeline.py
```

Expected: 5 results printed, each with a `saved →` line, and 5 `.md` files in `knowledge/raw/`.

```bash
ls knowledge/raw/
```

Expected: 5 files named like `2026-04-15_ir_chipotle_com_news-releases.md`

- [ ] **Step 3: Spot-check one file**

```bash
head -8 knowledge/raw/$(ls knowledge/raw/ | head -1)
```

Expected:
```
---
title: <title of first result>
url: https://...
date: 2026-04-15
---
```

---

### Task 5: Commit

**Files:** none

- [ ] **Step 1: Stage and commit**

```bash
git add scrape_pipeline.py tests/test_scrape_pipeline.py knowledge/raw/
git commit -m "feat: save Firecrawl results as dated markdown files in knowledge/raw/"
```
