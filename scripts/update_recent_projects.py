#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("GH_OWNER", "zjy4fun")
README_PATH = os.environ.get("README_PATH", "README.md")
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "5"))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

API = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed"


def github_get(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-updater"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fmt_date(iso_ts: str) -> str:
    # e.g. 2026-03-01T07:30:12Z -> 2026-03-01
    return iso_ts[:10]


def normalize_desc(desc: str | None) -> str:
    if not desc:
        return "最近有代码更新。"
    d = re.sub(r"\s+", " ", desc).strip()
    if len(d) > 80:
        d = d[:77].rstrip() + "..."
    return d


def build_items(repos):
    items = []
    for r in repos:
        name = r.get("name", "")
        if not name:
            continue
        if name.lower() == OWNER.lower():
            continue  # skip profile repo itself
        if r.get("fork"):
            continue
        if r.get("archived"):
            continue
        if r.get("disabled"):
            continue

        pushed = r.get("pushed_at", "")
        desc = normalize_desc(r.get("description"))
        url = r.get("html_url", f"https://github.com/{OWNER}/{name}")
        items.append((pushed, f"- [{name}]({url})  \n  {desc}（最近更新：{fmt_date(pushed)}）"))

    items.sort(key=lambda x: x[0], reverse=True)
    return [line for _, line in items[:MAX_ITEMS]]


def replace_block(text: str, block: str) -> str:
    pattern = re.compile(
        r"<!-- RECENT_PROJECTS_START -->(.*?)<!-- RECENT_PROJECTS_END -->",
        re.S,
    )

    def _repl(_: re.Match[str]) -> str:
        return f"<!-- RECENT_PROJECTS_START -->\n{block}\n<!-- RECENT_PROJECTS_END -->"

    return pattern.sub(_repl, text)


def main():
    repos = github_get(API)
    if not isinstance(repos, list):
        raise RuntimeError("Unexpected GitHub API response")

    lines = build_items(repos)
    block = "\n".join(lines) if lines else "- 暂无可展示项目"

    with open(README_PATH, "r", encoding="utf-8") as f:
        original = f.read()

    updated = replace_block(original, block)
    if updated != original:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
