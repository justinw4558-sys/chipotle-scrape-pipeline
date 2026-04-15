# Design: Save Firecrawl Results as Markdown Files

**Date:** 2026-04-15
**Scope:** Extend `scrape_pipeline.py` to persist each Firecrawl search result as a markdown file in `knowledge/raw/`.

---

## Approach

Inline extension of `scrape_pipeline.py` — no new files, no helper functions. Save logic is added directly inside the existing results loop.

---

## Filename Scheme

Derived from the result URL and the current date:

1. Strip the scheme (`https://` or `http://`)
2. Replace `.` and `/` with `_`
3. Prepend the ISO date

**Example:**
- URL: `https://ir.chipotle.com/news-releases`
- Date: `2026-04-15`
- Filename: `2026-04-15_ir_chipotle_com_news-releases.md`

---

## File Content

Each file contains a YAML front-matter block followed by the raw markdown body from Firecrawl.

```markdown
---
title: News Releases - Chipotle Mexican Grill
url: https://ir.chipotle.com/news-releases
date: 2026-04-15
---

<raw markdown from Firecrawl>
```

If a result has no markdown (`None` or empty string), the file is still written with the front-matter and an empty body — preserving a record that the URL was scraped.

---

## Output Directory

`knowledge/raw/` — created automatically via `Path.mkdir(parents=True, exist_ok=True)` if it does not exist.

---

## Overwrite Behavior

Always overwrite. Re-running the script is intentional and should produce fresh files.

---

## Code Changes

All changes are in `scrape_pipeline.py`:

- **Before the loop:** create `out_dir = Path("knowledge/raw")` and call `out_dir.mkdir(parents=True, exist_ok=True)`
- **Inside the loop:** build the filename from the URL + date, write front-matter + markdown body to `out_dir / filename`

No new imports required — `Path` is already imported. Existing `print` statements are unchanged.
