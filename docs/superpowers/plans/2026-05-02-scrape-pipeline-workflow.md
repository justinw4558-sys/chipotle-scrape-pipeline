# Scrape Pipeline GitHub Actions Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a GitHub Actions workflow that runs `scrape_pipeline.py` on a monthly schedule and commits new scraped markdown files in `knowledge/raw/` back to the repo.

**Architecture:** Single workflow file with one job. Job checks out the repo, installs Python deps, runs the script, then commits and pushes any new files in `knowledge/raw/` back to `main`. Manual trigger included for testing before the schedule fires.

**Tech Stack:** GitHub Actions, Python 3.12, `actions/checkout`, `actions/setup-python`

---

### Task 1: Create the workflow file

**Files:**
- Create: `.github/workflows/scrape-pipeline.yml`

- [ ] **Step 1: Create the workflows directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/scrape-pipeline.yml` with this exact content**

```yaml
name: Scrape Pipeline

on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 1 * *"  # 1st of every month at midnight UTC

permissions:
  contents: write

jobs:
  run-pipeline:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run scrape pipeline
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
        run: python scrape_pipeline.py

      - name: Commit new knowledge files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add knowledge/raw/
          git diff --cached --quiet || git commit -m "chore: add scraped knowledge files [skip ci]"
          git push
```

- [ ] **Step 3: Verify the file was created**

```bash
cat .github/workflows/scrape-pipeline.yml
```

Expected: full YAML printed with no errors.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/scrape-pipeline.yml
git commit -m "feat: add GitHub Actions workflow for scrape pipeline"
```

---

### Task 2: Push to GitHub and add the secret

**Files:**
- No file changes — GitHub UI configuration step

- [ ] **Step 1: Push the workflow to GitHub**

```bash
git push
```

Expected: branch pushed, no errors.

- [ ] **Step 2: Add the `FIRECRAWL_API_KEY` secret to the repo**

In your browser:
1. Go to your `chipotle-scrape-pipeline` repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `FIRECRAWL_API_KEY`
5. Value: your Firecrawl key (the `fc-...` value from your local `.env`)
6. Click **Add secret**

---

### Task 3: Run manually and verify

**Files:**
- No file changes — verification step

- [ ] **Step 1: Trigger the workflow manually**

In your browser:
1. Go to your `chipotle-scrape-pipeline` repo on GitHub
2. Click the **Actions** tab
3. Click **Scrape Pipeline** in the left sidebar
4. Click **Run workflow** → **Run workflow**

- [ ] **Step 2: Watch the run complete**

Wait for the run to finish (roughly 2-3 minutes — Firecrawl scrapes take longer than a weather API call). The run should show a green checkmark.

Click into the run and expand each step to confirm:
- "Run scrape pipeline" step shows results being saved to `knowledge/raw/`
- "Commit new knowledge files" step shows a commit was made

- [ ] **Step 3: Verify new files appeared on main**

```bash
git pull && git log --oneline -3
```

Expected: most recent commit is `chore: add scraped knowledge files [skip ci]` from `github-actions[bot]`.

- [ ] **Step 4: Verify the schedule is shown**

On the **Actions** tab → **Scrape Pipeline** workflow page, GitHub should display the schedule trigger. If it doesn't appear immediately, wait a few minutes — GitHub takes time to register new cron schedules.
