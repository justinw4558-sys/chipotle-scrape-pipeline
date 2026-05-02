# Mini-Project 04: Scrape Pipeline Tutorial

This is the written companion to Lesson 09. The lesson runs across two class sessions:

- **Session 01 (Wed Apr 22):** Concepts intro (20-min slides) + Firecrawl pipeline + MCP upgrade + project source. Steps 00–07.
- **Session 02 (Mon Apr 27):** Automate the API and scrape pipelines with GitHub Actions, then synthesize a knowledge base wiki from your scraped sources. Steps 08–14.

Use this if you fall behind, or to work through it on your own.

## Table of Contents

### Session 01: Scrape Pipeline (Wed Apr 22)

| Step | Topic | What You Will Do |
|------|-------|-----------------|
| 00 | [Create repo and start Claude Code](#step-00-create-github-repo-and-start-claude-code) | Set up the project repo, sign up for Firecrawl, create .env |
| 01 | [Search + Scrape Chipotle IR](#step-01-search--scrape-chipotle-ir) | Find pages and get their markdown in a single Firecrawl call |
| 02 | [Loop and save to knowledge/raw/](#step-02-loop-and-save-to-knowledgeraw) | Write one markdown file per result |
| 03 | [Install Firecrawl MCP](#step-03-install-firecrawl-mcp) | Add the Firecrawl MCP server to Claude Code |
| 04 | [Replicate the pipeline via one MCP prompt](#step-04-replicate-the-pipeline-via-one-mcp-prompt) | Issue a single directive that replaces ~30 lines of Python |
| 05 | [Find sources for your portfolio project](#step-05-find-sources-for-your-portfolio-project) | Open your project repo in a new Cursor window |
| 06 | [Scrape at least one source into your project](#step-06-scrape-at-least-one-source-into-your-project) | Apply the pattern to your own domain |
| 07 | [Commit and push](#step-07-commit-and-push) | Push both repos to GitHub |

### Session 02: Automate and Synthesize (Mon Apr 27)

| Step | Topic | What You Will Do |
|------|-------|-----------------|
| 08 | [Build your API pipeline workflow](#step-08-prompt-claude-code-to-build-your-api-pipeline-workflow) | Brainstorm + plan + implement the API automation |
| 09 | [Activate the schedule](#step-09-activate-the-schedule) | Add cron, verify on GitHub |
| 10 | [Automate the scrape pipeline](#step-10-automate-the-scrape-pipeline) | Repeat the pattern with commit-back permissions |
| 11 | [Design your wiki with Superpowers](#step-11-design-your-wiki-with-superpowers) | Brainstorm wiki structure, write a plan |
| 12 | [Generate the wiki pages](#step-12-generate-the-wiki-pages-with-executing-plans) | Use executing-plans to create wiki pages |
| 13 | [Make the wiki queryable](#step-13-make-the-wiki-queryable) | index.md + CLAUDE.md schema |
| 14 | [Use the wiki iteratively](#step-14-use-the-wiki-iteratively) | Demo ingest, lint, query→promote |

---

## Part 01: Setup

### Step 00: Create GitHub Repo and Start Claude Code

Same workflow as MP02 and MP03: create the repo on GitHub first, clone it into Cursor, then start building. This time you also sign up for Firecrawl first.

**What to do:**

1. Go to [github.com/new](https://github.com/new) and create a new repository:
   - Name it `chipotle-scrape-pipeline`
   - Set visibility to **Public**
   - Under **Add .gitignore**, select **Python** from the dropdown
   - Leave everything else as default
   - Click **Create repository**

2. On your new repository's GitHub page, click the green **Code** button, make sure **HTTPS** is selected, and copy the URL.

3. Clone the repo into Cursor: new window → **Clone repo** → paste the URL → save under your `isba-4715` folder.

   ```
   ~/isba-4715/
   ├── campus-bites-pipeline/     <-- MP01
   ├── basket-craft-pipeline/     <-- MP02
   ├── weather-api-pipeline/      <-- MP03
   └── chipotle-scrape-pipeline/   <-- MP04
   ```

4. Open a terminal in Cursor (`` Ctrl+` `` or **Terminal > New Terminal**) and start Claude Code:
   ```bash
   claude
   ```

5. Ask Claude Code to set up the environment:

   ```
   Set up a Python venv and install requests, python-dotenv.
   ```

   `requests` makes HTTP calls to Firecrawl (same library as MP03's Weather API), `python-dotenv` loads your `.env` keys.

   The install takes 30-60s. **While it runs, sign up in your browser (step 6).** To run Python outside Claude Code later: `source venv/bin/activate` (Mac) or `venv\Scripts\activate` (Windows).

6. **Sign up for Firecrawl** at [firecrawl.dev](https://firecrawl.dev). **Use your LMU `.edu` email** (not GitHub OAuth) so the student-program coupon can verify your school email in the next step. Create a password, confirm via email, then open **Dashboard → API Keys** and copy the `fc-...` key.

7. Create `.env` in your project root. Replace the placeholder with your actual key:

   ```
   FIRECRAWL_API_KEY=fc-your_firecrawl_key_here
   ```

8. Verify `.env` is in your `.gitignore` — **before your first commit**. The Python template already includes it; if not, add `.env` on its own line.

**Why `.env` instead of pasting keys into code?** MP03 hardcoded the WeatherAPI key into `weather.py` — fine for a demo, but any commit would leak the key to a public repo. From MP04 forward, keys live in `.env` (gitignored), loaded at runtime with `os.getenv()`. Same pattern as the async Spotify tutorial.

**Why Firecrawl:** Firecrawl is a single API that combines web search with automatic markdown extraction. One call gives you a ranked list of URLs and the cleaned markdown content of each page. Older tutorials use two services (one for search, one for scraping), but Firecrawl's [`search` endpoint](https://docs.firecrawl.dev/features/search) does both in one round-trip.

**Free tier:** 500 Firecrawl credits on signup — plenty for this lesson. If you applied the student coupon (see below) you have 20,000 instead.

**Student credits:** Firecrawl's [Student Program](https://www.firecrawl.dev/student-program) gives students 20,000 free credits (40× the default). **Two steps to redeem:** (1) sign up with your `.edu` email in step 6, not GitHub OAuth; (2) in the Firecrawl dashboard, open **Settings → Billing** and enter the coupon `STUDENTEDU`. The default 500 credits cover this lesson, but 20k carries you through Milestone 02's scheduled runs.

**Checkpoint:** Your `chipotle-scrape-pipeline` repo is cloned, Claude Code confirms the virtual environment has `requests` and `python-dotenv` installed, your `.env` file contains your Firecrawl API key, and `.env` is listed in your `.gitignore`.

---

## Part 02: Python Pipeline — Firecrawl

### Step 01: Search + Scrape Chipotle IR

Find pages worth scraping and get their markdown in a single call. Firecrawl's `search` endpoint runs a web query, then automatically scrapes each result page. You send a query, you get back a list of URLs with titles, descriptions, and cleaned markdown content.

Demo target: **Chipotle Investor Relations (IR)** content. IR pages are public by legal requirement and include press releases, leadership bios, and earnings material — the kind of content a knowledge base needs.

**SDK or raw HTTP?** Firecrawl publishes a Python SDK called `firecrawl-py`, and most of their docs use it. This tutorial uses raw `requests` instead — the same pattern MP03 used for WeatherAPI. Two reasons: you already know `requests` from MP03, and HTTP endpoints are more stable than SDK versions (we hit an SDK import-path break while writing this tutorial). Under the hood the SDK is doing `requests.post()` too. If you later want the SDK for a project, `pip install firecrawl-py` and swap it in — the request body we build below matches what the SDK sends.

**What to do:**

1. In Cursor, create `scrape_pipeline.py`. Save it (`Cmd+S` / `Ctrl+S`).

2. **Copy** these imports:

   ```python
   import os
   import re
   import time
   from pathlib import Path
   from dotenv import load_dotenv
   import requests
   ```

   `re`, `time`, and `Path` are used in Step 02.

3. **Type** these lines to load your key and create the client:

   ```python
   load_dotenv()

   api_key = os.getenv("FIRECRAWL_API_KEY")
   ```

   `load_dotenv()` reads `.env` into the environment so `os.getenv("KEY")` can retrieve values. Your key never appears in the source.

4. **Copy** this code below the client setup. It builds the request, sends it, and prints the raw response so you can see exactly what Firecrawl sent back:

   ```python
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

   print(response)
   print(response.text)
   ```

   Each line has a specific job, same shape as MP03's Weather API call:
   - `api_url` — the endpoint you are hitting.
   - `headers` — a dict of HTTP headers. Firecrawl authenticates via `Authorization: Bearer <your-key>` instead of a `?key=...` URL parameter like WeatherAPI used.
   - `payload` — the request body. Goes as JSON because this is a `POST`, not a `GET`.
   - `requests.post()` — sends the HTTP POST request and returns the response.

5. **Save** and run. Two ways to do this:

   - **Ask Claude Code to run it.** Type something like `run scrape_pipeline.py`. Claude Code uses the venv automatically.
   - **Run it yourself in the terminal.** First activate the venv: `source venv/bin/activate` (Mac) or `venv\Scripts\activate` (Windows). Then:

     ```bash
     python scrape_pipeline.py
     ```

     If you skip the activate step, you will hit `ModuleNotFoundError: No module named 'dotenv'` because the system Python cannot see the venv's packages.

   You should see `<Response [200]>` (the Response object's repr — the `200` inside means the call succeeded) followed by a wall of JSON — the raw search results with titles, URLs, and scraped markdown for each page. It is dense and hard to read, which is exactly why the next step parses it.

6. **Replace** `print(response)` and `print(response.text)` with parsing logic that turns the JSON into usable data and prints a clean summary:

   ```python
   data = response.json()
   results = data["data"]["web"]
   print(f"Firecrawl returned {len(results)} results")

   for r in results:
       print(f"  - {r['title']}")
       print(f"    {r['url']}")
       print(f"    markdown length: {len(r.get('markdown') or '')} chars")
   ```

   - `response.json()` — converts the JSON string from the previous step into a Python dictionary.
   - `data["data"]["web"]` — drills into the nested structure to get the list of search results. The outer `data` key holds the payload; `web` holds the list you iterate.
   - Each `r` in the loop is a dict with keys like `title`, `url`, `description`, and `markdown`.

7. **Save** and run the script again. You should now see five results, each with a title, a URL from `chipotle.com` or `ir.chipotle.com`, and a non-zero markdown length. The search found the pages and scraped them in a single call.

**Why `limit=5`:** Keeps the demo fast and your credit budget low. In your project you might ask for 20 or 50.

**What the response looks like:** Firecrawl returns JSON with `{"success": true, "data": {...}, "creditsUsed": N}`. The results you want live at `data["data"]["web"]` — a list of dicts, each with `url`, `title`, `description`, and `markdown` keys. To see the full shape, add `print(data)` after the `response.json()` line.

**Why `"scrapeOptions": {"formats": ["markdown"]}`:** Firecrawl can return HTML, markdown, summaries, screenshots, or links. Markdown preserves headings/lists/tables without HTML noise — right for a knowledge base. Note the JSON uses `scrapeOptions` in camelCase (Firecrawl's API convention), not `scrape_options`.

**Boilerplate is normal:** Some scraped pages include cookie banners or footers. Claude Code synthesizes across many sources and ignores repeated boilerplate — collect sources, do not polish extractions.

**Troubleshooting:** Check `response.status_code` before trusting the body — `200` means success, `401` means bad API key, `402` means out of credits, `429` means rate-limited. If it is anything other than `200`, print `response.json()` and read the error. If a specific result has `markdown == None`, that page failed to scrape (move on — next step handles this case).

**Checkpoint:** Your script prints five Chipotle IR results with titles, URLs, and non-zero markdown lengths. Results vary from run to run — any five entries from `chipotle.com` or `ir.chipotle.com` domains means you succeeded.

### Step 02: Loop and Save to `knowledge/raw/`

You have five results with markdown already attached — search and scrape happened in Step 01's single call. This step loops over them and writes one markdown file per result.

You wrote the API call by hand in Step 01 so you understand what is happening. For this step, you hand the loop-and-save work to Claude Code. This is the real workflow: you build the parts that require judgment, the AI writes the boilerplate around them — and in this case, you also practice letting the AI help you *design* the boilerplate before it writes any code.

**What to do:**

1. **Start a brainstorming session.** Paste this into Claude Code:

   ```
   I want to extend scrape_pipeline.py so it saves each Firecrawl
   search result as a markdown file in knowledge/raw/. Help me
   decide how.
   ```

   This deliberately gives Claude Code almost nothing to go on. If the `superpowers:brainstorming` skill is installed, Claude Code should recognize the open-ended phrasing, refuse to start writing code, and ask clarifying questions one at a time — things like: *How should filenames be named? What goes at the top of each file? What happens if a result has no markdown?* Answer each question as it comes.

   If you do not have Superpowers installed, this step still works — Claude Code will just ask fewer questions up front. Either way, the goal is the same: talk through the design, then let Claude Code implement it.

2. **Open `scrape_pipeline.py` in Cursor and read the new Step 02 block Claude Code wrote.** Do not accept it blindly. Walk through the code line by line and ask yourself:

   - Does it create `knowledge/raw/` if the folder does not exist yet?
   - Does it loop over the `results` list from your Step 01 code?
   - How does it turn each result's title into a filename?
   - What happens if a result has no markdown content?
   - Does it include the source URL somewhere so you can trace each file back to its origin?

   If the answer to any of these is unclear or unsatisfying, go back to Claude Code and ask it to explain or change it. Reading AI-generated code and deciding whether it does what you asked is the skill you are practicing here — it matters more than the writing.

3. **Save** and run (same two ways as Step 01 — ask Claude Code, or activate the venv first, then `python scrape_pipeline.py`).

   You should see up to five files being written. Open `knowledge/raw/` in Cursor to inspect them.

**Why brainstorm instead of copy-paste?** A well-specified prompt is itself an engineering skill. If your initial request is vague ("save the results to files"), a good AI collaborator should not jump straight to code — it should surface the decisions hiding in your request (filenames? headers? empty-result handling?) and let you answer them. That is the whole point of the `superpowers:brainstorming` skill: turn an idea into a design through dialogue, *then* implement. You practiced that here. In your portfolio project, you will use the same move for every non-trivial feature.

**When the brainstorm asks about filenames:** Search results can share titles — Firecrawl sometimes returns multiple pages titled "News Releases." A title-based slug alone causes filename collisions. Tell Claude Code to prefix filenames with a zero-padded index (`01-`, `02-`) so each file is unique and sorts in order.

**When the brainstorm asks about the file header:** Ask for the source URL at the top of each file. That provenance is what lets Claude Code cite where each fact came from when it later reads `knowledge/raw/` to write your wiki pages.

**When the brainstorm asks about empty results:** Firecrawl may return `None` for the markdown field if a specific page could not be rendered. Tell Claude Code to skip those instead of writing empty files — a zero-byte file is worse than no file.

**Checkpoint:** You have up to five markdown files in `knowledge/raw/`, each with a title header, source URL, and scraped content. If a result's markdown was empty, the script skipped it. This is the full Python pipeline: **search + scrape → loop → save**.

---

## Part 03: MCP Upgrade

### Step 03: Install Firecrawl MCP

Install the Firecrawl MCP server so Claude Code can call Firecrawl directly, no Python needed.

**What is MCP?** MCP stands for **Model Context Protocol** — a way to plug external tools into an AI agent. Anthropic published the spec; Firecrawl, GitHub, and many others publish MCP servers that expose their services to Claude Code. When you install an MCP server, its tools show up alongside Claude Code's built-in tools, and you can invoke them in plain prompts. Think of MCPs as "apps for Claude Code."

**What to do:**

1. **Install the Firecrawl MCP server.** First, return to your regular shell prompt: inside Claude Code, type `exit` (or press `Ctrl+D`) to leave the Claude Code session. You should now see your shell prompt (`$` on Mac, `>` on Windows). Cursor's built-in terminal panel is fine — you do not need a new window.

   **Before running the next command, replace `YOUR_FIRECRAWL_KEY` in the URL with your actual `fc-...` key from `.env`.** Copy-paste, then edit the URL in your terminal before pressing Enter:

   ```bash
   claude mcp add --transport http --scope user firecrawl https://mcp.firecrawl.dev/YOUR_FIRECRAWL_KEY/v2/mcp
   ```

   You should see a confirmation message that the server was added.

2. **Restart Claude Code** in your `chipotle-scrape-pipeline` repo terminal:

   ```bash
   claude
   ```

3. **Verify the MCP is connected.** Inside Claude Code, type:

   ```
   /mcp
   ```

   You should see `firecrawl` listed as `✔ connected`. If it shows an error, check the command you used (typos in the URL or key are the most common cause).

**Why `--scope user`?** The Firecrawl MCP install embeds your key in the server URL. Project scope would write that URL (and key) into `.claude/settings.json` inside your public repo. User scope writes to `~/.claude/` instead — keys stay off GitHub. Same principle as Step 00's `.env`.

**Heads-up:** The MCP install is a one-time thing per machine. You do not need to reinstall this MCP for future projects — it will be available in any Cursor window where you run Claude Code.

**Checkpoint:** `/mcp` inside Claude Code shows `firecrawl` as `✔ connected`. If it fails, exit Claude Code, check the install command you ran, and re-run it.

### Step 04: Replicate the Pipeline via One MCP Prompt

The Python pipeline is ~30 lines. This step collapses it into one prompt via the Firecrawl MCP you installed in Step 03. Same result, zero code.

**What to do:**

1. Make sure you are in the `chipotle-scrape-pipeline` repo directory with Claude Code running.

2. Paste this prompt:

   ```
   Use the firecrawl search tool to find 5 URLs about Chipotle's
   executive leadership team and senior hires, scraping each as
   markdown. Save each result to knowledge/raw/ with filenames like
   leadership-NN-slug.md (zero-padded index, title-based slug).
   Include the source URL at the top of each file.
   ```

3. Watch:
   - Claude Code picks the right Firecrawl MCP tool
   - Loops over the returned results
   - Writes markdown files to `knowledge/raw/`

   No Python. No `requests.post`. No `os.getenv`. Claude Code is the executor.

4. Check `knowledge/raw/` in Cursor's file explorer. You should see the `leadership-NN-slug.md` files that Claude Code created, alongside the `NN-slug.md` files your Python script already saved in Step 02. Your knowledge base just grew by five entries covering a different content type (leadership, not press releases), and you only wrote one sentence of instruction.

**Which tool will Claude Code actually call?** The Firecrawl MCP server exposes several tools — the one that combines search and scraping has a name you do not need to memorize. Claude Code will pick the right one from your natural-language prompt. If you want to see what is available, type `/mcp` inside Claude Code to list every connected tool.

**Why the filename format in the prompt:** Precise naming prevents Claude Code from inventing its own. The `leadership-` prefix also keeps MCP-created files separate from the `NN-slug.md` press-release files Step 02 saved. Different query, different prefix, different content — same knowledge base.

**Why this matters for your project:** Milestone 02 needs ≥15 sources in `knowledge/raw/` from 3+ sites, automated via GitHub Actions. Use MCP to explore your domain, then formalize the best sources into a Python pipeline. MCP for exploration, Python for production.

**When to use Python vs MCP:**

| Situation | Use | Why |
|---|---|---|
| Scheduled, automated production pipeline | Python | Fixed response schema, deterministic parameters, easy to version and test |
| Exploring an unfamiliar domain before committing to a pipeline | MCP | One prompt beats 30 lines of code when you do not yet know what to collect |
| Adding known sources you found manually | MCP | Fast, no code to maintain for a handful of URLs |
| Reproducible collection that must run the same way every day | Python | Deterministic, version-controlled, testable |

**If something goes wrong:**

- **The Firecrawl tool is not listed:** Check `/mcp` inside Claude Code. If `firecrawl` is not `✔ connected`, revisit Step 03's install command. You may need to restart Claude Code (`exit`, then `claude` again).
- **Claude Code writes files to the wrong place:** Claude Code interprets paths relative to the current directory. Confirm you ran `claude` from inside your `chipotle-scrape-pipeline` repo (not your portfolio project, not your home directory). If files landed in the wrong folder, run `pwd` to see where Claude Code is, then tell it: `Move the leadership-NN-slug.md files you just created into knowledge/raw/ under the current directory.`

**Checkpoint:** You see up to 5 new `leadership-NN-slug.md` files in `knowledge/raw/` that Claude Code created via the MCP tool, without you writing any Python. If a scrape returned empty content, Claude Code may have skipped that result — fewer than 5 files is normal for the same reasons Step 02 noted. This is the same pipeline you wrote in Part 02, issued as one sentence instead of ~30 lines of code.

---

## Part 04: Project Connection

Part 04 has 20 minutes. If you are running short on time, skip Step 05's brainstorming prompt and jump directly to Step 06 Option B using a domain topic you already know. Step 07 (commit and push) is required regardless — leave time for it.

### Step 05: Find Sources for Your Portfolio Project

You are done with the `chipotle-scrape-pipeline` demo repo. For the rest of class, you will work inside [your portfolio project](https://github.com/LMU-ISBA/isba-4715-f26/tree/main/project) repo — applying the same pattern to your own domain.

Your project's knowledge base needs at least 15 sources from 3+ different sites by Milestone 02. Today you are getting at least one. The pattern is the same as what you just did with Chipotle; only the query changes. You can add more throughout the week.

**What to do:**

1. Open a **new Cursor window** (**File > New Window**). Clone your portfolio project repo into it the same way you did for `chipotle-scrape-pipeline` in Step 00. Start Claude Code in the terminal.

2. You are now working in your portfolio project repo, not the scrape pipeline. If your portfolio repo does not have a `knowledge/raw/` folder yet, create one:

   ```bash
   mkdir -p knowledge/raw
   ```

3. Brainstorm source candidates with Claude Code. The prompt below references `docs/job-posting.pdf` and `docs/proposal.md` — if your portfolio repo does not yet have those files, either add them now or remove those references from the prompt before pasting:

   ```
   I'm building a portfolio project targeting a [job title] role in
   [industry]. Based on my job posting (in docs/job-posting.pdf) and
   my proposal (in docs/proposal.md), suggest 5 unstructured web
   sources I should scrape into my knowledge base. For each source,
   give me a Firecrawl search query I could use.
   ```

4. Pick one source to scrape right now. You can scrape more async this week.

**If your target site blocks scraping:** Some sites (LinkedIn full profiles, many SaaS dashboards, sites behind aggressive Cloudflare) return 403 errors or empty content through Firecrawl. Public fallbacks that almost always work:

- Company investor relations pages (`ir.<company>.com`)
- SEC filings ([sec.gov/cgi-bin/browse-edgar](https://www.sec.gov/cgi-bin/browse-edgar))
- Press release archives (PR Newswire, Business Wire, GlobeNewswire)
- Wikipedia
- Seeking Alpha earnings call transcripts (free tier previews only — full transcripts require an account)
- Company blog posts and newsroom pages

**Checkpoint:** You have identified at least one specific URL or site pattern relevant to your portfolio project. Write it down in a scratch note or terminal comment — you will use it in Step 06.

---

### Step 06: Scrape at Least One Source into Your Project

**What to do:**

1. You have two ways to scrape into your portfolio repo's `knowledge/raw/`. **For the remaining class time, use Option B — it is faster and you already have Claude Code running with the Firecrawl MCP connected.** Option A is the approach you will formalize for GitHub Actions later in your project, so you may prefer it async this week.

   **Option B — use the MCP prompt.** In your portfolio repo's Claude Code session, paste a prompt similar to Step 04's, but with your own query. Example:

   ```
   Use the firecrawl search tool to find 3 URLs about [your industry
   topic] and scrape each as markdown. Save each result to knowledge/raw/
   with filenames like NN-slug.md. Include the source URL at the top
   of each file.
   ```

   **Option A — reuse your Python script.** Follow this sequence exactly — the ordering matters so your key never reaches git:

   1. Open your portfolio repo's `.gitignore` and confirm `.env` is listed. If it is not, add `.env` on its own line and save the file.
   2. Only then copy `scrape_pipeline.py` and `.env` from your `chipotle-scrape-pipeline` repo into your portfolio repo.
   3. Run `git status` in your portfolio repo. If `.env` appears as an untracked file in the output, your gitignore is wrong — stop and fix it before continuing.
   4. Change the Firecrawl query in the script to something relevant to your project, then run it.

2. Confirm at least one new `.md` file appears in your portfolio repo's `knowledge/raw/`. Open it and verify the content is relevant to your domain — not every scrape is useful, and this is the moment to catch sources that will not help your knowledge base.

**Why source quality matters:** Milestone 02's wiki grade comes from what Claude Code synthesizes from `knowledge/raw/`. Cookie banners produce bad wikis; real press releases and earnings content produce wikis you can defend in your final interview.

**Checkpoint:** Your portfolio project repo has one or more markdown files in `knowledge/raw/` scraped from a real source relevant to your job posting.

---

### Step 07: Commit and Push

**What to do:**

You have two Cursor windows open (one per repo). Run each step in its respective window.

1. In the `chipotle-scrape-pipeline` Claude Code session, first run `git status` yourself in the terminal and look at the staged-and-untracked file list. If you see `.env` listed anywhere, STOP — your gitignore is missing `.env` and you need to fix it before continuing.

2. Once `git status` is clean, use Claude Code to finish the commit:

   ```
   Save pip freeze to requirements.txt, then commit all files and
   push to GitHub. Before staging, run `git status` and abort if .env
   appears in the output.
   ```

3. In the portfolio repo's Claude Code session, run `git status` yourself first. Again, confirm no `.env` entry. Then use Claude Code:

   ```
   Commit the new files in knowledge/raw/ and push to GitHub. Before
   staging, run `git status` and abort if .env appears in the output.
   ```

4. Verify both repos on GitHub. Open each repo's root directory in the GitHub file browser and confirm:
   - `knowledge/raw/` is visible and contains your markdown files
   - `.env` does NOT appear in the root file listing

**Checkpoint:** Both repos are pushed, and the GitHub root file listing for each shows no `.env` file.

---

## Part 05: Automate the Pipelines (Session 02)

> Session 02 teaches automation and wiki synthesis using your existing demo repos from earlier lessons, then asks you to apply the same patterns to your portfolio repo for Milestone 02. Steps 08–09 automate the weather pipeline in your `weather-api-pipeline` repo (from Lesson 08). Step 10 repeats the pattern for the scrape pipeline in your `chipotle-scrape-pipeline` repo (from Session 01). Steps 11–14 build the knowledge base wiki in your portfolio repo using the sources you scraped for Milestone 01.

### Step 08: Prompt Claude Code to Build Your API Pipeline Workflow

Time to put your weather pipeline (from Lesson 08) on autopilot. You'll use the Superpowers skills to design the workflow first, then implement what the design produces.

**What to do:**

1. **Open a new Cursor window** (**File > New Window**). Open your `weather-api-pipeline` repo there. Start a fresh Claude Code session in the terminal.
2. Trigger the **brainstorming** skill. Paste this into Claude Code:

   ```
   I want to put my weather pipeline on a schedule using GitHub Actions.
   Help me design the workflow.
   ```

   Let Claude Code drive the conversation from there. You'll surface requirements you wouldn't have thought of unprompted: run cadence, what to do on failure, what counts as a successful run, manual vs. scheduled triggers, where credentials live.

   **One thing the brainstorm should flag:** in Lesson 08 you hardcoded the API key in `weather.py` as a Python string. That won't work in GitHub Actions. The runner is a public CI environment, and the workflow needs to read the key from a secret rather than from a literal string in the source. Refactoring `weather.py` to use `os.getenv("WEATHER_API_KEY")` will be part of the plan.
3. When the brainstorm settles, the Superpowers chain transitions into **writing-plans**. Follow Claude Code's prompts as the plan takes shape. Expect the resulting plan to cover:
   - Refactoring `weather.py` to read the API key from an environment variable
   - Creating the workflow file (typically `.github/workflows/weather-pipeline.yml`)
   - Adding the API key as a GitHub Actions secret
4. Have Claude Code execute the plan: refactor `weather.py`, write the workflow file.
5. Add the secret your script now reads to your repo. **The rule: only copy variables your script actually reads.** Don't bulk-copy from anywhere.

   To identify which secrets to add:
   - Open the script the workflow runs. Find every `os.getenv("...")` call. Those names are exactly the secrets you need.
   - **Skip any variable whose value contains `localhost`.** GitHub Actions runners are fresh VMs with no local services running. A workflow trying to connect to `localhost` will fail with a confusing connection error.

   Then in GitHub:
   - Go to your repo → **Settings** → **Secrets and variables** → **Actions**.
   - Click **New repository secret**.
   - For each variable from your script, paste the variable name into **Name** (must match exactly) and the value into **Secret**. Click **Add secret**.

   For `weather.py`, this is just one secret: `WEATHER_API_KEY` (the variable name your refactor introduced).

   For your portfolio's API → Snowflake loader (your M02 follow-up), expect more. Typically 7 Snowflake secrets (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`) plus the API key.
6. Commit the refactored script and the workflow file, then push to GitHub.
7. On GitHub → Actions tab → run the workflow manually. Verify the run finishes green and the run logs show the expected number of rows collected.

**Why this matters:** This is the same flow you'd use in your first analytics engineering job. Brainstorm requirements before specifying behavior, specify before planning, plan before writing code. The hardcoded-key refactor is exactly the kind of issue the brainstorm should catch *before* you write a single line of YAML. Caught after, you'd have committed a broken workflow and confused yourself debugging it.

**Checkpoint:** Your `weather-api-pipeline` workflow runs successfully on manual trigger from the GitHub Actions tab. `weather.py` no longer has the API key hardcoded, it now reads from `os.getenv("WEATHER_API_KEY")`. The brainstorm and plan are committed somewhere in your repo (your call where: `docs/`, `plans/`, or wherever you decide makes sense).

### Step 09: Activate the Schedule

Your workflow runs on manual trigger. Time to make it run without you. The cadence decision matters more than it looks: it affects API rate limits, compute cost, and how fresh your data is.

**What to do:**

1. Open your implementation plan from Step 08. Did it specify a schedule cadence? If yes, you have your answer. If no, paste this into Claude Code:

   ```
   What schedule cadence makes sense for this pipeline?
   ```

   Settle on a cadence before moving on.
2. Update the workflow YAML to add the `schedule:` trigger alongside `workflow_dispatch`. Push.
3. Verify on GitHub: Actions tab → your workflow → the page should mention "This workflow has a schedule."

**Why this matters:** Cron is a promise to run later. Manual is run now. You always want manual first so you can see the green check before trusting the schedule. Now that manual works, you can wire the cron with confidence.

**Checkpoint:** Your workflow file has a `schedule:` block, GitHub shows the schedule on the workflow page, and you've recorded *why* you picked this cadence (in the plan, in a commit message, or both).

### Step 10: Automate the Scrape Pipeline

For repetition's sake, you'll automate the scrape pipeline in your `chipotle-scrape-pipeline` repo (from Session 01) with another fresh Claude Code session. Same pattern as Step 08, but the new session doesn't know what you did for the weather workflow, so the prompt has to stand on its own.

**What to do:**

1. **Open a new Cursor window** (**File > New Window**). Open your `chipotle-scrape-pipeline` repo there. Start a fresh Claude Code session in the terminal.
2. Trigger the **brainstorming** skill. Paste this into Claude Code:

   ```
   I want to put my Firecrawl scrape pipeline on a schedule using GitHub
   Actions. Help me design the workflow.
   ```

   Notice the prompt has to stand on its own. This Claude Code session has no memory of Steps 08 and 09. You should hear about `permissions: contents: write` and a commit/push step at the end.
3. When the brainstorm settles, the chain transitions into **writing-plans**. Follow Claude Code's prompts as the plan takes shape.
4. Follow the plan. Add the `FIRECRAWL_API_KEY` secret to the `chipotle-scrape-pipeline` repo's Settings → Secrets and variables → Actions. Commit the workflow file. Push to GitHub.
5. Run it manually from the Actions tab. Verify (a) the workflow finishes green, and (b) new markdown files appear in `knowledge/raw/` on your `main` branch.
6. Once manual works, activate the schedule.
7. **For Milestone 02:** apply this same pattern to your portfolio repo's scrape pipeline. You can do this in remaining class time, in office hours, or async during the week. The M02 rubric requires both your API and scrape pipelines automated in your portfolio repo.

**Why this matters:** Running the brainstorm-and-plan loop a second time in a fresh Claude Code session is the rep that locks the pattern in. The first time (Step 08), Claude Code had the context of your `weather-api-pipeline` repo and your prior conversation. This time, the agent has nothing, and you have to give it just enough to design well. That's the skill that transfers to every new project: knowing what minimum context to provide an empty session.

**Checkpoint:** Both your `weather-api-pipeline` workflow (from Steps 08–09) and your `chipotle-scrape-pipeline` workflow (from this step) show green on Actions and have schedules attached. The chipotle repo's `knowledge/raw/` has new files from the scrape workflow's run.

---

## Part 06: Build the Knowledge Base Wiki

> Part 06 happens in your **portfolio repo**, where the scraped sources from Milestone 01 already live in `knowledge/raw/`. Switch back to the Cursor window with your portfolio repo open, or open a new window for it if you don't have one.

### Step 11: Design Your Wiki with Superpowers

You've got 15+ scraped sources in `knowledge/raw/`. Time to turn them into something useful, not just a folder of files. The wiki helps you build out the project and understand the role your project is based on. It feeds two things: the analytical decisions in your dashboard (what to investigate, why), and your readiness to talk about the role in a real interview.

**What to do:**

Before you start, **make sure your job-posting PDF is saved at `docs/job-posting.pdf`** in your portfolio repo. The prompts below reference it via `@docs/job-posting.pdf`, so the path needs to match.

**No job posting yet?** Use the [in-class demo posting](https://to.indeed.com/aay4mbm8ygdp) (Manager, Workforce Management - Volume & Labor at Chipotle). Open the link, then `Cmd+P` / `Ctrl+P` → **Save as PDF**, and save it to your portfolio repo as `docs/job-posting.pdf`.

1. Ask Claude Code to explore your scraped sources. Paste this into Claude Code:

   ```
   Read everything in @knowledge/raw/ and tell me what's there: what
   each source covers, where they overlap, where they conflict, and
   what's notably missing for someone applying to the role in
   @docs/job-posting.pdf
   ```

   The `@` prefix tells Claude Code to read the referenced files as context, not just see them as strings. You wouldn't get this from a 2-minute skim, but Claude Code can do it in seconds.
2. Trigger the **brainstorming** skill. Paste this into Claude Code:

   ```
   Help me design a knowledge base wiki built from these sources, scoped
   to the role in @docs/job-posting.pdf. The wiki should help me talk
   about the role intelligently and inform the analytics-related questions.
   ```

   Let the skill drive the design conversation from there.
3. The brainstorm should help you decide: what does someone in this role need to know to be effective? What hiring-manager questions should the wiki prepare you for? Which patterns from the sources should shape the dashboard questions you investigate? Which 3+ wiki pages cover all that without bloating?
4. When the design settles, the chain transitions into **writing-plans**, which produces a plan naming each wiki page, the role-relevant questions it answers, and how it gets generated. Follow Claude Code's prompts as the plan takes shape.

**Why this matters:** Most students treat the knowledge base as a checklist deliverable: 15 sources, 3 wiki pages, done. The students who get A-range work treat it as project fuel and interview prep. The wiki shapes what their dashboard analyzes and what they can speak to confidently in their final interview. Same content, different intent. The brainstorm is what locks in the intent.

**Checkpoint:** A plan committed to your repo that names your wiki pages, the role-focused questions each one answers, the hiring-manager questions this wiki would help you handle, and your sourcing convention. No wiki content yet.

### Step 12: Generate the Wiki Pages with executing-plans

Now you implement what the plan from Step 11 describes. Each wiki page is one task on the plan, and the **executing-plans** skill is built to walk through plans like this with review checkpoints.

**What to do:**

1. Stay in the same Claude Code session where you completed the plan in Step 11. After **writing-plans** finishes, the Superpowers chain transitions into **executing-plans**, which walks through each wiki page in turn with review checkpoints. Just follow Claude Code's prompts back to you. You don't need to paste anything new.
2. At each checkpoint, review what it produced. Spot-check the citations against the actual source files in `knowledge/raw/`. Push back on anything that reads like summary instead of synthesis. Insist on source citations for every non-obvious claim.
3. Refine and continue until all wiki pages on the plan are written to `knowledge/wiki/`.

**Why this matters:** This is where synthesis vs. summary becomes visible. A summary page reads like a table of contents: "this source says X, that source says Y." A synthesis page reads like an analyst's brief: "across these sources, the pattern is Z, and where they disagree, here's why." The executing-plans skill's checkpoint structure gives you natural moments to push back on summary-shaped output, which Claude Code defaults to without resistance.

**Checkpoint:** All wiki pages from your plan are committed to `knowledge/wiki/`. Each has source citations you've spot-checked. Reading any one page should give you a real answer to a domain question, not a list of source summaries.

### Step 13: Make the Wiki Queryable

Wiki pages alone aren't a queryable knowledge base. You need two more things: an index Claude Code reads first to know what's available, and a schema in `CLAUDE.md` that documents how Claude Code (and any future LLM you point at this repo) should ingest, query, and maintain the wiki.

**What to do:**

1. Generate `knowledge/index.md`. Paste this into Claude Code:

   ```
   Write knowledge/index.md as a categorical catalog of every wiki page.
   Group by category (overview, key entities or themes, synthesis, or
   whatever fits), one-line summary per page, with cross-references where
   wiki pages link to each other.
   ```

   The index is what Claude Code reads first when you ask a domain question. It should help the agent decide which wiki page to open without scanning everything.
2. Add a "Knowledge base schema" section to your repo's `CLAUDE.md` documenting three operations the agent should follow when working with the wiki. Paste this into Claude Code:

   ```
   Add a "Knowledge base schema" section to my CLAUDE.md documenting
   three operations: ingest (when new sources land in knowledge/raw/),
   query (when answering domain questions), and lint (periodic
   consistency checks). Word them however fits my domain.
   ```

   The schema should cover these three operations:
   - **Ingest:** when a new source lands in `knowledge/raw/`, read it, summarize it into the relevant wiki page(s), update `index.md`, commit with a meaningful message.
   - **Query:** when asked about [your domain or role], read `index.md` first, follow cross-references into `knowledge/wiki/`, drill into `knowledge/raw/` only when direct evidence or quotes are needed.
   - **Lint:** "linting" in software means automated quality checks on code, like catching unused variables or style violations. Wiki linting borrows the same idea: periodically scan the wiki for quality issues that drift as the corpus grows. For a wiki, that means checking for contradictions across pages, stale claims, orphan pages (wiki pages no other page links to), and missing cross-references.

   Make sure a fresh Claude Code session (with no prior context) would follow it.
3. Test the schema. Open a clean Claude Code session (or use `/clear`), then paste this into Claude Code:

   ```
   What does my knowledge base say about the company's main growth
   drivers and biggest operational challenges?
   ```

   This question generalizes to any company in any industry. Swap it for something more specific if your domain calls for it.

   Watch what files it opens. If it follows index → wiki → raw, the schema works. If it ignores `index.md` and grabs random files from `knowledge/raw/`, refine the wording.

**Why this matters:** This step turns a folder of files into a *system*. The wiki is a persistent, compounding artifact: every new source you ingest makes it richer, and periodic lint keeps it consistent over time. The bookkeeping (summaries, cross-references, schema enforcement) is what the agent owns forever. Your job stays curation: pick the sources, ask the questions, review what comes back. Skip the schema and you're back to scanning raw files every time you have a question.

**Checkpoint:** `knowledge/index.md` exists, organized by category, with cross-references between wiki pages. `CLAUDE.md` has a "Knowledge base schema" section covering ingest, query, and lint. A clean Claude Code session, asked a domain question, follows the index → wiki → raw navigation order and produces a useful answer.

### Step 14: Use the Wiki Iteratively

A wiki you build once and never touch is a snapshot. A wiki you maintain is an asset. This step is three quick demos of the wiki in motion: ingest, lint, query-promote. Each one is a habit you'll repeat over the next 8 days as you polish your portfolio for M02.

**What to do:**

1. **Ingest (~3 min).** Find one new source for your domain (use the Firecrawl MCP server in Claude Code for speed, or scrape one URL via your script). Add it to `knowledge/raw/`. Then paste this into Claude Code:

   ```
   I just added a new source to knowledge/raw/. Run the Ingest operation
   from CLAUDE.md.
   ```

   Watch the wiki update in real time.
2. **Lint (~3 min).** Paste this into Claude Code:

   ```
   Run the Lint operation from my CLAUDE.md schema.
   ```

   Pick one finding and fix it. Commit.
3. **Query → promote (~3 min).** Paste this into Claude Code:

   ```
   What does my knowledge base say about [a hard domain question that
   doesn't have a clean answer in the existing wiki]?
   ```

   Once it produces a synthesis from the raw sources, **consider saving the answer as part of the wiki.** Promoting good answers into wiki pages means Claude Code doesn't have to re-derive them from raw sources next time you (or a hiring manager) asks the same question. If the answer is worth keeping, paste this into Claude Code:

   ```
   Promote that answer into a new wiki page (or expand an existing one).
   Update knowledge/index.md.
   ```

   Commit.

**Why this matters:** This is the rubric requirement for "evidence of iterative use, visible in commit history" (M02 #11), but the deeper point is that the wiki only earns its place in your portfolio if it's *alive*. A static wiki is checkbox work. A wiki that grows over the next 8 days, with commits showing meaningful edits and fixes, is what differentiates A-range work from B-range. The three operations from Step 13's schema are not theoretical. They're the moves you'll repeat dozens of times before May 4.

**Checkpoint:** Three new commits, each demonstrating a different schema operation. `knowledge/wiki/` shows clear evidence of iterative editing. Plan to repeat at least one of these operations every other day until M02 submission.

---

## Submission

LE09 spans both class sessions and produces deliverables in two repos. Submit your `chipotle-scrape-pipeline` repo URL on Brightspace; your portfolio repo work counts toward Milestones 01 and 02.

### `chipotle-scrape-pipeline` repo (Session 01 + Session 02 Step 10)

Your `chipotle-scrape-pipeline` repo should contain:
- `scrape_pipeline.py` — your Firecrawl pipeline (Session 01)
- `knowledge/raw/` — at least 5 `NN-slug.md` files from the Python pipeline (Step 02) AND at least 1 `leadership-NN-slug.md` file from the MCP prompt (Step 04). Both naming patterns are expected.
- `requirements.txt` — Python dependencies
- `.gitignore` — Python gitignore (must exclude `.env`)
- `.github/workflows/scrape-pipeline.yml` — automated workflow added in Session 02 Step 10 (manual + scheduled triggers)

Your `chipotle-scrape-pipeline` repo must NOT contain:
- `.env` — must be gitignored, no keys in git history

### `weather-api-pipeline` repo (updated in Session 02 Step 08)

Your existing `weather-api-pipeline` repo from Lesson 08 picks up two updates:
- `weather.py` — refactored in Session 02 Step 08 to read the API key from `os.getenv("WEATHER_API_KEY")` instead of hardcoding it
- `.github/workflows/weather-pipeline.yml` — automated workflow added in Session 02 Step 08 (manual + scheduled triggers)

### Portfolio project repo (Session 02 wiki work + M02 follow-up)

Session 02 wiki work in your portfolio repo contributes to Milestone 02 (due May 4):
- `knowledge/wiki/` with at least 3 wiki pages aligned with your job posting and role (Steps 11–12)
- `knowledge/index.md` — categorical catalog with cross-references (Step 13)
- `CLAUDE.md` "Knowledge base schema" section covering ingest, query, and lint (Step 13)
- The plans your brainstorms produced, committed somewhere in the repo (Steps 11 onward)

**For Milestone 02:** apply the GitHub Actions patterns from Steps 08–10 to your portfolio repo's API loader and scrape pipeline. The M02 rubric requires both pipelines automated in your portfolio repo with manual + scheduled triggers.

You built two automated pipelines, refactored hardcoded credentials into proper secrets handling, and produced a queryable knowledge base. You also practiced the brainstorm → plan → execute loop twice in fresh Claude Code sessions.
