#!/usr/bin/env python3
"""Render YoungJurry's self-hosted, activity-aware profile signal as SVG."""

from __future__ import annotations

import json
import os
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
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


def contribution_data(token: str):
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
        from datetime import timedelta
        cursor -= timedelta(days=1)
    streak = 0
    from datetime import timedelta
    while values.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def shorten(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"


def render(repos: list[dict], total_contributions: int, days: list[dict]) -> str:
    owned = [repo for repo in repos if not repo.get("fork") and repo["name"] != USERNAME]
    latest = sorted(owned, key=lambda repo: repo.get("pushed_at") or "", reverse=True)
    stars = sum(repo.get("stargazers_count", 0) for repo in owned)
    languages = Counter(repo["language"] for repo in owned if repo.get("language"))
    top_languages = " / ".join(language for language, _ in languages.most_common(4)) or "Exploring"
    streak = current_streak(days)

    last_push = datetime.fromisoformat(latest[0]["pushed_at"].replace("Z", "+00:00")) if latest else datetime.now(timezone.utc)
    push_age = (datetime.now(timezone.utc) - last_push).days
    state = "ACTIVE" if push_age <= 3 else "IDLE"
    state_cn = "在线构建中" if state == "ACTIVE" else "等待新信号"
    status_color = "#56d364" if state == "ACTIVE" else "#d29922"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    recent_rows = []
    for index, repo in enumerate(latest[:3]):
        y = 262 + index * 28
        pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).strftime("%m-%d")
        language = repo.get("language") or "mixed"
        recent_rows.append(
            f'<text x="72" y="{y}" class="repo">{escape(shorten(repo["name"], 27))}</text>'
            f'<text x="350" y="{y}" class="muted">{escape(language)} · {pushed}</text>'
        )

    recent_days = days[-28:]
    maximum = max((item["contributionCount"] for item in recent_days), default=1) or 1
    bars = []
    for index, item in enumerate(recent_days):
        height = 5 if item["contributionCount"] == 0 else 5 + round(29 * item["contributionCount"] / maximum)
        x = 70 + index * 17
        y = 367 - height
        opacity = 0.20 if item["contributionCount"] == 0 else 0.55 + 0.45 * item["contributionCount"] / maximum
        bars.append(f'<rect x="{x}" y="{y}" width="10" height="{height}" rx="2" fill="#58a6ff" opacity="{opacity:.2f}"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="390" viewBox="0 0 900 390" role="img" aria-labelledby="title desc">
<title id="title">YoungJurry live developer signal</title>
<desc id="desc">A bilingual terminal dashboard generated from live GitHub activity.</desc>
<style>
  :root {{ --bg:#f6f8fa; --panel:#ffffff; --text:#1f2328; --muted:#656d76; --line:#d0d7de; --blue:#0969da; --purple:#8250df; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --panel:#161b22; --text:#e6edf3; --muted:#8b949e; --line:#30363d; --blue:#58a6ff; --purple:#bc8cff; }} }}
  .bg {{ fill:var(--bg) }} .panel {{ fill:var(--panel); stroke:var(--line) }}
  text {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; fill:var(--text) }}
  .muted {{ fill:var(--muted); font-size:12px }} .label {{ fill:var(--muted); font-size:11px; letter-spacing:1.5px }}
  .value {{ font-size:23px; font-weight:700 }} .repo {{ font-size:14px; font-weight:600 }}
  .blue {{ fill:var(--blue) }} .purple {{ fill:var(--purple) }}
  .cursor {{ animation:blink 1.05s steps(2,end) infinite }}
  .bot {{ animation:float 2.8s ease-in-out infinite; transform-box:fill-box; transform-origin:center }}
  .antenna {{ animation:pulse 1.5s ease-in-out infinite }}
  @keyframes blink {{ 50% {{ opacity:0 }} }}
  @keyframes float {{ 50% {{ transform:translateY(-4px) }} }}
  @keyframes pulse {{ 50% {{ opacity:.25 }} }}
</style>
<rect class="bg" width="900" height="390" rx="14"/>
<rect class="panel" x="18" y="18" width="864" height="354" rx="12"/>
<circle cx="42" cy="42" r="5" fill="#ff5f56"/><circle cx="59" cy="42" r="5" fill="#ffbd2e"/><circle cx="76" cy="42" r="5" fill="#27c93f"/>
<text x="100" y="47" class="label">YJ://SIGNAL — LIVE PROFILE TELEMETRY / 实时档案信号</text>
<line x1="36" y1="62" x2="864" y2="62" stroke="var(--line)"/>

<text x="54" y="96" font-size="17" font-weight="700">youngshine@github:~$ ./whoami</text><rect x="363" y="82" width="9" height="18" class="blue cursor"/>
<circle cx="59" cy="119" r="4" fill="{status_color}" class="antenna"/>
<text x="72" y="124" font-size="13" fill="{status_color}">{state} · {state_cn}</text>
<text x="72" y="145" class="muted">Linux desktop × AI agent tooling / Linux 桌面 × AI 智能体工具</text>

<rect class="panel" x="54" y="164" width="121" height="49" rx="7"/><text x="66" y="181" class="label">REPOS</text><text x="66" y="204" class="value blue">{len(owned)}</text>
<rect class="panel" x="184" y="164" width="121" height="49" rx="7"/><text x="196" y="181" class="label">STARS</text><text x="196" y="204" class="value blue">{stars}</text>
<rect class="panel" x="314" y="164" width="121" height="49" rx="7"/><text x="326" y="181" class="label">COMMITS+</text><text x="326" y="204" class="value blue">{total_contributions}</text>
<rect class="panel" x="444" y="164" width="121" height="49" rx="7"/><text x="456" y="181" class="label">STREAK</text><text x="456" y="204" class="value blue">{streak}d</text>

<text x="54" y="231" class="label">RECENT TRANSMISSIONS / 最近信号</text>
{''.join(recent_rows)}
<text x="54" y="341" class="label">28-DAY CONTRIBUTION PULSE / 28 日贡献脉冲</text>
{''.join(bars)}

<g class="bot" transform="translate(670 112)">
  <circle cx="72" cy="0" r="7" fill="{status_color}" class="antenna"/><rect x="69" y="7" width="6" height="17" fill="var(--muted)"/>
  <rect x="28" y="23" width="88" height="68" rx="10" fill="var(--panel)" stroke="var(--blue)" stroke-width="3"/>
  <rect x="39" y="36" width="66" height="36" rx="5" fill="var(--bg)" stroke="var(--line)"/>
  <rect x="51" y="48" width="10" height="10" rx="2" fill="var(--blue)"/><rect x="83" y="48" width="10" height="10" rx="2" fill="var(--purple)"/>
  <rect x="58" y="66" width="28" height="3" rx="1" fill="var(--muted)"/>
  <rect x="18" y="42" width="10" height="31" rx="4" fill="var(--blue)"/><rect x="116" y="42" width="10" height="31" rx="4" fill="var(--purple)"/>
  <rect x="40" y="91" width="22" height="10" rx="3" fill="var(--blue)"/><rect x="82" y="91" width="22" height="10" rx="3" fill="var(--purple)"/>
  <text x="72" y="123" text-anchor="middle" class="label">JURRY-01</text>
  <text x="72" y="143" text-anchor="middle" class="muted">ENERGY {total_contributions % 100:02d}%</text>
</g>

<text x="852" y="355" text-anchor="end" class="muted">{escape(top_languages)}</text>
<text x="852" y="367" text-anchor="end" class="muted" font-size="9">UPDATED {now}</text>
</svg>'''


def main():
    token = os.getenv("GH_TOKEN", "") or os.getenv("GITHUB_TOKEN", "")
    repos = request(f"{API}/users/{USERNAME}/repos?per_page=100&type=owner", token)
    total, days = contribution_data(token)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(repos, total, days), encoding="utf-8")
    print(f"Rendered {OUT}")


if __name__ == "__main__":
    main()
