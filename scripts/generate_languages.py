"""Builds languages.svg (green/black theme) from the public repos of a GitHub user.

Runs inside GitHub Actions. Uses only the Python standard library.
"""
import json
import os
import urllib.request
from xml.sax.saxutils import escape

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "FebiReena")
TOKEN = os.environ.get("GH_TOKEN", "")
OUTPUT = "languages.svg"
SKIP_REPOS = {OWNER.lower()}          # skip the profile repo itself
COLORS = ["#39d353", "#26a641", "#006d32", "#7ee787"]
MAX_LANGS = 4


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def collect_languages():
    totals = {}
    repos = api(f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner")
    for repo in repos:
        if repo.get("fork") or repo["name"].lower() in SKIP_REPOS:
            continue
        for lang, size in api(repo["languages_url"]).items():
            totals[lang] = totals.get(lang, 0) + size
    return totals


def render(totals):
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:MAX_LANGS]
    total = sum(size for _, size in top) or 1
    bar_x, bar_w = 25, 350

    segments, legend = [], []
    x = bar_x
    for i, (lang, size) in enumerate(top):
        pct = size / total * 100
        w = bar_w * size / total
        color = COLORS[i % len(COLORS)]
        segments.append(f'<rect x="{x:.1f}" y="58" width="{w:.1f}" height="8" fill="{color}"/>')
        if i > 0:
            segments.append(f'<rect x="{x - 1:.1f}" y="58" width="2" height="8" fill="#0d1117"/>')
        x += w
        col, row = i % 2, i // 2
        cx, cy = 32 + col * 180, 92 + row * 26
        legend.append(
            f'<circle cx="{cx}" cy="{cy}" r="5" fill="{color}"/>'
            f'<text x="{cx + 13}" y="{cy + 4.5}">{escape(lang)} {pct:.2f}%</text>'
        )

    rows = (len(top) + 1) // 2
    height = 100 + rows * 26
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}" viewBox="0 0 400 {height}" fill="none" role="img" aria-label="Most used languages">
  <defs><clipPath id="bar"><rect x="{bar_x}" y="58" width="{bar_w}" height="8" rx="4"/></clipPath></defs>
  <rect x="0.5" y="0.5" width="399" height="{height - 1}" rx="4.5" fill="#0d1117" stroke="#0e4429"/>
  <text x="25" y="35" font-family="Segoe UI, Ubuntu, Sans-Serif" font-size="18" font-weight="600" fill="#39d353">Most Used Languages</text>
  <g clip-path="url(#bar)">{"".join(segments)}</g>
  <g font-family="Segoe UI, Ubuntu, Sans-Serif" font-size="13" fill="#c9d1d9">{"".join(legend)}</g>
</svg>
'''


if __name__ == "__main__":
    langs = collect_languages()
    if not langs:
        raise SystemExit("No language data found; leaving the existing file unchanged.")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(render(langs))
    print("Wrote", OUTPUT)
