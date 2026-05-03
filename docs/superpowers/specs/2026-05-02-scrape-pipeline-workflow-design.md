# Scrape Pipeline GitHub Actions Workflow — Design Spec

**Date:** 2026-05-02
**Repo:** chipotle-scrape-pipeline

---

## Goal

Automate `scrape_pipeline.py` to run on a monthly schedule via GitHub Actions, committing any new scraped markdown files in `knowledge/raw/` back to the repo after each run. Failures must be visible (red run, not silently swallowed).

---

## Triggers

- `workflow_dispatch` — manual trigger for testing before trusting the schedule
- `schedule` — cron `0 0 1 * *` (1st of every month at midnight UTC)

---

## Workflow Structure

Single job on `ubuntu-latest`.

**Steps:**
1. Checkout repo (`actions/checkout`)
2. Set up Python 3.12 (`actions/setup-python`)
3. Install dependencies (`pip install -r requirements.txt`)
4. Run `scrape_pipeline.py` — non-zero exit fails the job visibly
5. Commit new files in `knowledge/raw/` with message `chore: add scraped knowledge files [skip ci]` and push

**Permissions:** `contents: write` (required for the commit-back step)

**`[skip ci]` tag:** Prevents the commit from triggering another workflow run loop.

---

## Secrets

One secret required: `FIRECRAWL_API_KEY`

- Add via: repo → Settings → Secrets and variables → Actions → New repository secret
- `scrape_pipeline.py` already reads it via `os.getenv("FIRECRAWL_API_KEY")` — no code changes needed

---

## Key Difference from Weather Workflow

The weather pipeline overwrites one CSV file per run. This pipeline writes new dated files each run (`YYYY-MM-DD_slug.md`), so `git add knowledge/raw/` will always have new files to stage after a successful scrape.

---

## Error Handling

If `scrape_pipeline.py` exits with a non-zero status code (bad key, Firecrawl outage, network error), the job fails and GitHub marks the run red. No silent failures.

---

## File Written

`.github/workflows/scrape-pipeline.yml`

---

## Success Criteria

- Manual trigger runs green and new dated markdown files appear in `knowledge/raw/` on `main`
- GitHub Actions tab shows the schedule attached to the workflow
- `.env` does not appear anywhere in the workflow file or repo
