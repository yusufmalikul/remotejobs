#!/usr/bin/env python3
"""
find_jobs.py  <job-posting-URL>  [--out ./jobs]

• Downloads the raw HTML of the page
• Sends it to Gemini with a structured-JSON prompt
• Saves Gemini’s JSON reply verbatim to ./jobs/YYYY-MM-DD-slug.json
"""

import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
import google.generativeai as genai

# ----------------------------------------------------------------------
# 1)  Gemini set-up
# ----------------------------------------------------------------------
GEN_KEY = os.getenv("GEMINI_API_KEY")
if not GEN_KEY:
    sys.exit("❌  Set GEMINI_API_KEY in your environment (or .env).")

genai.configure(api_key=GEN_KEY)
MODEL = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

# ----------------------------------------------------------------------
def make_prompt(html: str) -> str:
    """Prompt that forces Gemini to respond with a *single* JSON object."""
    return f"""
You are an information-extraction engine.

From the HTML job-posting below, identify the following fields and return
**EXACTLY** one JSON object without markdown, code fences, or commentary.

Schema (**keys must appear in this order**):

{{
  "job_title"       : string | null,
  "company"         : string | null,
  "posted_date"     : string | null,      # ISO-8601  YYYY-MM-DD or null
  "requirements"    : string | null,      # main description
  "salary_annual"   : string | null,
  "company_country" : string | null,
  "company_address" : string | null,
  "classification"  : "remote_worldwide" | "remote_timezone" | null
}}

• For *classification* choose:
    – **remote_worldwide**  → role can be performed from anywhere on earth
    – **remote_timezone**   → remote but restricted to a region/country/offset
    – If unclear, use null.

• Use **null** for any unknown / missing value.

↓  BEGIN HTML ↓
{html}
↑  END HTML ↑
""".strip()


def extract_json(html: str) -> dict:
    """Ask Gemini to produce the JSON blob. Retries once on bad JSON."""
    prompt = make_prompt(html)
    rsp = MODEL.generate_content(prompt)
    txt = rsp.text.strip()

    # Gemini sometimes adds triple-backticks; strip them
    if txt.startswith("```"):    # remove ```json … ```
        txt = txt.strip("`").lstrip("json").strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # one retry with a stricter follow-up
        follow = MODEL.generate_content(
            "Respond ONLY the valid JSON (no markdown, no comments).",
            conversation=rsp
        ).text.strip()
        follow = follow.strip("`").lstrip("json").strip()
        return json.loads(follow)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="Job posting URL")
    ap.add_argument("--out", default="./jobs", help="Output directory")
    args = ap.parse_args()

    html = requests.get(args.url, timeout=30).text
    data = extract_json(html)

    # add two useful meta-fields
    data["source_url"] = args.url
    data["scraped_at"] = datetime.now(timezone.utc).isoformat()

    # filename: posted-date if we have it, else today
    date_part = (data.get("posted_date") or datetime.utcnow().date().isoformat())
    slug = os.path.splitext(Path(urlparse(args.url).path).name)[0][:40]
    out_file = Path(args.out) / f"{date_part}-{slug}.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✓ wrote", out_file)


if __name__ == "__main__":
    main()
