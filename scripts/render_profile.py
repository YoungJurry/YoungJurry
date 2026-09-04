#!/usr/bin/env python3
"""Render an activity-aware profile cover using only GitHub's API."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

USERNAME = "YoungJurry"
API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
OUT = Path("dist/profile-signal.svg")


def request(url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if payload:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def contributions(token: str):
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { contributionCount date } }
          }
        }
      }
    }
    """
    result = request(GRAPHQL, token, {"query": query, "variables": {"login": USERNAME}})
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return calendar["totalContributions"], days


def current_streak(days: list[dict]) -> int:
    values = {date.fromisoformat(day["date"]): day["contributionCount"] for day in days}
    cursor = datetime.now(timezone.utc).date()
    if values.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)
    streak = 0
    while values.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def shorten(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"


def render(repos: list[dict], total: int, days: list[dict]) -> str:
    owned = [repo for repo in repos if not repo.get("fork") and repo["name"] != USERNAME]
    latest = sorted(owned, key=lambda repo: repo.get("pushed_at") or "", reverse=True)
    stars = sum(repo.get("stargazers_count", 0) for repo in owned)
    streak = current_streak(days)

    latest_name = shorten(latest[0]["name"], 28) if latest else "initializing"
    last_push = datetime.fromisoformat(latest[0]["pushed_at"].replace("Z", "+00:00")) if latest else datetime.now(timezone.utc)
    active = (datetime.now(timezone.utc) - last_push).days <= 3
    state = "ONLINE / 构建中" if active else "STANDBY / 待机"
    status = "#5ee787" if active else "#e3b341"
    energy = total % 100
    circumference = 2 * 3.14159 * 57
    dash = circumference * energy / 100
    updated = datetime.now(timezone.utc).strftime("%Y.%m.%d")

    metrics = [
        ("REPOSITORIES", "仓库", str(len(owned))),
        ("TOTAL STARS", "星标", str(stars)),
        ("CONTRIBUTIONS", "年度贡献", str(total)),
        ("CURRENT STREAK", "连续贡献", f"{streak}d"),
    ]
    metric_svg = []
    for index, (label, cn, value) in enumerate(metrics):
        x = 56 + index * 207
        if index:
            metric_svg.append(f'<line x1="{x - 20}" y1="287" x2="{x - 20}" y2="331" class="divider"/>')
        metric_svg.append(
            f'<text x="{x}" y="298" class="metric-label">{label} · {cn}</text>'
            f'<text x="{x}" y="329" class="metric-value">{escape(value)}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360" role="img" aria-labelledby="title desc">
<title id="title">YoungJurry — Linux and AI agent developer</title>
<desc id="desc">A minimal cyber profile cover generated from live GitHub activity.</desc>
<defs>
  <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0d121b"/><stop offset="0.58" stop-color="#0a0e15"/><stop offset="1" stop-color="#101526"/>
  </linearGradient>
  <linearGradient id="brand" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="#58a6ff"/><stop offset="1" stop-color="#a78bfa"/>
  </linearGradient>
  <radialGradient id="glow" cx="75%" cy="40%" r="58%">
    <stop offset="0" stop-color="#315cff" stop-opacity=".16"/><stop offset="1" stop-color="#315cff" stop-opacity="0"/>
  </radialGradient>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
    <path d="M24 0H0V24" fill="none" stroke="#58a6ff" stroke-opacity=".055"/>
  </pattern>
  <filter id="soft-glow" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="card-clip"><rect x="646" y="77" width="198" height="174" rx="16"/></clipPath>
</defs>
<style>
  text {{ font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif }}
  .mono {{ font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace }}
  .muted {{ fill:#7d8799 }} .divider {{ stroke:#273044 }}
  .metric-label {{ fill:#667085; font:600 9px "SFMono-Regular",Consolas,monospace; letter-spacing:1px }}
  .metric-value {{ fill:#e8edf5; font:600 23px Inter,ui-sans-serif,sans-serif }}
  .blink {{ animation:blink 1.15s steps(2,end) infinite }}
  .float {{ animation:float 3.2s ease-in-out infinite; transform-box:fill-box; transform-origin:center }}
  .scan {{ animation:scan 4.5s linear infinite }}
  .signal {{ animation:signal 1.8s ease-in-out infinite }}
  @keyframes blink {{ 50% {{ opacity:.15 }} }}
  @keyframes float {{ 50% {{ transform:translateY(-5px) }} }}
  @keyframes scan {{ from {{ transform:translateY(-40px) }} to {{ transform:translateY(210px) }} }}
  @keyframes signal {{ 50% {{ opacity:.35 }} }}
</style>

<rect width="900" height="360" rx="16" fill="url(#surface)"/>
<rect width="900" height="360" rx="16" fill="url(#grid)"/>
<rect width="900" height="360" rx="16" fill="url(#glow)"/>
<rect x="1" y="1" width="898" height="358" rx="15" fill="none" stroke="#283247"/>
<path d="M1 76V16A15 15 0 0 1 16 1h115" fill="none" stroke="#58a6ff" stroke-width="2"/>
<path d="M899 284v60a15 15 0 0 1-15 15H769" fill="none" stroke="#8b5cf6" stroke-width="2"/>

<!-- top signal bar -->
<circle cx="38" cy="35" r="4" fill="{status}" filter="url(#soft-glow)" class="signal"/>
<text x="51" y="39" fill="{status}" font-size="11" font-weight="700" letter-spacing="1.3">{state}</text>
<text x="450" y="39" text-anchor="middle" class="mono muted" font-size="10" letter-spacing="2">YJ // OPEN SOURCE SIGNAL</text>
<text x="862" y="39" text-anchor="end" class="mono muted" font-size="10">NODE 01 · {updated}</text>
<line x1="28" y1="57" x2="872" y2="57" stroke="#202a3c"/>

<!-- identity -->
<text x="54" y="93" class="mono" fill="#667085" font-size="11" letter-spacing="2.5">HELLO, I AM / 你好，我是</text>
<text x="50" y="154" fill="#f0f4fa" font-size="54" font-weight="800" letter-spacing="-2">YOUNG<tspan fill="url(#brand)">JURRY</tspan></text>
<rect x="54" y="169" width="62" height="3" rx="1.5" fill="url(#brand)"/>
<text x="128" y="176" fill="#b9c2d0" font-size="14" font-weight="600" letter-spacing="1.6">LINUX DESKTOP × AI AGENT TOOLING</text>
<text x="54" y="207" fill="#8994a7" font-size="13">把桌面体验、开发者工具与 AI 智能体连接起来。</text>
<text x="54" y="239" class="mono" fill="#667085" font-size="12">$ now_building </text>
<text x="160" y="239" class="mono" fill="#69b4ff" font-size="12">{escape(latest_name)}</text>
<rect x="{166 + min(len(latest_name), 28) * 7}" y="228" width="7" height="14" rx="1" fill="#a78bfa" class="blink"/>

<!-- mascot module -->
<rect x="646" y="77" width="198" height="174" rx="16" fill="#0c111b" fill-opacity=".78" stroke="#29334a"/>
<text x="664" y="99" class="mono muted" font-size="9" letter-spacing="1.3">COMPANION // JURRY-01</text>
<circle cx="745" cy="164" r="57" fill="none" stroke="#202a3b" stroke-width="3"/>
<circle cx="745" cy="164" r="57" fill="none" stroke="url(#brand)" stroke-width="3" stroke-linecap="round"
  stroke-dasharray="{dash:.1f} {circumference - dash:.1f}" transform="rotate(-90 745 164)"/>
<g transform="translate(695 116)"><g class="float">
  <rect x="47" y="0" width="6" height="15" rx="3" fill="#63708a"/><circle cx="50" cy="0" r="5" fill="{status}" class="signal"/>
  <rect x="14" y="14" width="72" height="58" rx="12" fill="#151d2c" stroke="#58a6ff" stroke-width="2"/>
  <rect x="25" y="27" width="50" height="27" rx="6" fill="#090d14"/>
  <rect x="34" y="35" width="8" height="8" rx="2" fill="#69b4ff" filter="url(#soft-glow)"/>
  <rect x="58" y="35" width="8" height="8" rx="2" fill="#a78bfa" filter="url(#soft-glow)"/>
  <path d="M40 59h20" stroke="#63708a" stroke-width="3" stroke-linecap="round"/>
  <rect x="2" y="30" width="12" height="27" rx="5" fill="#293650"/><rect x="86" y="30" width="12" height="27" rx="5" fill="#293650"/>
  <rect x="27" y="72" width="17" height="8" rx="3" fill="#58a6ff"/><rect x="56" y="72" width="17" height="8" rx="3" fill="#8b5cf6"/>
</g></g>
<text x="745" y="233" text-anchor="middle" class="mono" fill="#7d8799" font-size="9" letter-spacing="1">ENERGY {energy:02d}%</text>
<g clip-path="url(#card-clip)"><rect x="647" y="77" width="196" height="2" fill="#58a6ff" opacity=".35" class="scan"/></g>

<!-- live metrics -->
<rect x="28" y="268" width="844" height="70" rx="12" fill="#0b1019" fill-opacity=".88" stroke="#202a3c"/>
{''.join(metric_svg)}
</svg>'''


def main():
    token = os.getenv("GH_TOKEN", "") or os.getenv("GITHUB_TOKEN", "")
    repos = request(f"{API}/users/{USERNAME}/repos?per_page=100&type=owner", token)
    total, days = contributions(token)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(repos, total, days), encoding="utf-8")
    print(f"Rendered {OUT}")


if __name__ == "__main__":
    main()
