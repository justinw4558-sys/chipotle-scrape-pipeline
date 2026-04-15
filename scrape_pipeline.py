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

data = response.json() # Convert the response to a JSON object
results = data["data"]["web"] # Get the results from the response
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