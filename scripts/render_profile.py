#!/usr/bin/env python3
"""A quiet, bilingual profile cover. No external rendering services."""
from __future__ import annotations

import base64
import json
import math
import os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
USERNAME = "YoungJurry"


def repositories(token: str) -> list[dict]:
    """Read public owned repos, including subsequent pages."""
    result = []
    for page in range(1, 101):
        request = Request(
            f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError("Repository pagination exceeded safety limit")


def latest_project(repos: list[dict]) -> tuple[str, str]:
    candidates = [repo for repo in repos if not repo.get("fork")
                  and not repo.get("private") and not repo.get("archived")
                  and repo["name"].lower() != USERNAME.lower() and repo.get("pushed_at")]
    if not candidates:
        return "Exploring new ideas", ""
    latest = max(candidates, key=lambda repo: repo["pushed_at"])
    name = latest["name"]
    if len(name) > 30:
        name = name[:29] + "…"
    return name, datetime.fromisoformat(latest["pushed_at"].replace("Z", "+00:00")).strftime("%Y.%m.%d")


def ribbon() -> str:
    """Projected Möbius strip: a single continuous surface, drawn as fine threads."""
    lines = []
    for index in range(16):
        v = index * 2.6
        points = []
        # A 4π traversal closes each thread without a seam.
        for step in range(361):
            t = 4 * math.pi * step / 360
            r = 115 + v * math.cos(t / 2)
            x = r * math.cos(t)
            y = r * math.sin(t) * .57 + v * math.sin(t / 2) * .95
            # A slight tilt creates the diagonal sculptural silhouette.
            points.append(f"{x * .91 - y * .41:.2f},{x * .41 + y * .91:.2f}")
        lines.append(f'<path d="M{" L".join(points)} Z"/>')
    return "\n".join(lines)


def render(repos: list[dict], theme: str) -> str:
    dark = theme == "dark"
    bg, fg, secondary, muted, line, blue = (
        ("#101215", "#f1f3f5", "#aeb5c0", "#858e9d", "#2b3038", "#7faaff") if dark else
        ("#fafbfc", "#171d27", "#4e5b70", "#657188", "#dce1e9", "#326be0")
    )
    font_css = []
    for weight, name in [(400, "Regular"), (700, "Bold")]:
        data = base64.b64encode((ROOT / f"assets/JetBrainsMono-{name}.ttf").read_bytes()).decode()
        font_css.append(f'@font-face{{font-family:JB;src:url(data:font/ttf;base64,{data}) format("truetype");font-weight:{weight}}}')
    project, pushed = latest_project(repos)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="440" viewBox="0 0 1000 440" role="img" aria-labelledby="title desc">
<title id="title">youngshine / YoungJurry</title>
<desc id="desc">Small tools. Better workflows. 小工具，让日常更顺手。Linux, Wayland and AI tooling. Latest project: {escape(project)}.</desc>
<defs>
  <linearGradient id="ink" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="{blue}" stop-opacity=".25"/>
    <stop offset=".48" stop-color="{blue}" stop-opacity=".95"/>
    <stop offset="1" stop-color="{blue}" stop-opacity=".35"/>
  </linearGradient>
  <clipPath id="bounds"><rect width="1000" height="440" rx="18"/></clipPath>
</defs>
<style>
{''.join(font_css)}
text{{font-family:JB,"JetBrains Mono","JetBrainsMono Nerd Font","Noto Sans CJK SC","Microsoft YaHei",monospace;fill:{fg}}}
.secondary{{fill:{secondary}}}.muted{{fill:{muted}}}.blue{{fill:{blue}}}
.sculpture{{animation:breathe 14s ease-in-out infinite;transform-origin:0 0}}
.trace{{animation:travel 9s linear infinite;stroke-dasharray:22 160;stroke-dashoffset:0}}
@keyframes breathe{{0%,100%{{transform:translateY(0) rotate(-5deg)}}50%{{transform:translateY(-7px) rotate(5deg)}}}}
@keyframes travel{{to{{stroke-dashoffset:-364}}}}
@media(prefers-reduced-motion:reduce){{.sculpture,.trace{{animation:none}}}}
</style>
<g clip-path="url(#bounds)">
<rect width="1000" height="440" fill="{bg}"/>
<rect x=".5" y=".5" width="999" height="439" rx="17.5" fill="none" stroke="{line}"/>

<!-- Editorial masthead: one accent, no dashboard chrome. -->
<path d="M52 47h18m-9-9v18" stroke="{blue}" stroke-width="2"/>
<text x="84" y="52" font-size="13" letter-spacing="1.5">YOUNGJURRY</text>
<text x="948" y="52" text-anchor="end" class="muted" font-size="12">A PERSONAL WORKSPACE</text>

<text x="51" y="164" font-size="65" font-weight="700" letter-spacing="-3.8">youngshine<tspan class="blue">.</tspan></text>
<text x="54" y="220" font-size="21" class="secondary" letter-spacing="-.6">Small tools. Better workflows.</text>
<text x="54" y="255" font-size="17" class="secondary">小工具，让日常更顺手。</text>
<text x="54" y="311" font-size="12" class="muted" letter-spacing=".8">LINUX / WAYLAND / AI TOOLING</text>

<!-- Abstract, slow-moving continuous ribbon. -->
<g transform="translate(787 207)">
  <g class="sculpture" fill="none" stroke="url(#ink)" stroke-width=".65">{ribbon()}</g>
</g>

<path d="M54 353H946" stroke="{line}"/>
<path d="M54 353H946" class="trace" stroke="{blue}" stroke-width="1" opacity=".4"/>
<text x="54" y="393" class="muted" font-size="12">LATEST PUSH / 最近更新</text>
<text x="258" y="393" font-size="13">{escape(project)}</text>
<text x="946" y="393" text-anchor="end" class="muted" font-size="12">{pushed}</text>
</g>
</svg>'''


def main():
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN or GITHUB_TOKEN")
    repos = repositories(token)
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = out / f"cover-editorial-{theme}.svg"
        path.write_text(render(repos, theme), encoding="utf-8")
        print(f"Rendered {path}")


if __name__ == "__main__":
    main()
