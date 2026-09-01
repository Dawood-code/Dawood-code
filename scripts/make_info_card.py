"""Generate Dawood's animated neofetch-style profile card."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "info-card.svg"

PROFILE = [
    ("name", "Muhammad Dawood"),
    ("role", "Web · App · Game Developer"),
    ("now", "React + React Native"),
    ("stack", "JavaScript · Python · C++"),
    ("home", "Lahore, Pakistan"),
    ("open_to", "collaboration & useful products"),
    ("offscreen", "anime · football · Hala Madrid"),
]


def main() -> None:
    static = os.getenv("STATIC") == "1"
    lines: list[str] = []
    for index, (key, value) in enumerate(PROFILE):
        y = 100 + index * 34
        style = "" if static else f' style="animation-delay:{0.34 + index * 0.11:.2f}s"'
        lines.append(
            f'<g class="line"{style}><text class="key" x="30" y="{y}">{escape(key)}</text>'
            f'<text class="colon" x="122" y="{y}">:</text>'
            f'<text class="value" x="142" y="{y}">{escape(value)}</text></g>'
        )

    animation = "" if static else "opacity:0;transform:translateX(-8px);animation:print .42s ease forwards;"
    blink = "" if static else '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" />'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="490" height="352" viewBox="0 0 490 352" role="img" aria-labelledby="title desc">
  <title id="title">Muhammad Dawood developer card</title>
  <desc id="desc">A terminal-style summary of Muhammad Dawood's role, stack, and interests.</desc>
  <style>
    text {{ font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace; }}
    .line {{ {animation} }}
    .key {{ fill:#56d364; font-size:13px; font-weight:700; }}
    .colon {{ fill:#8b949e; font-size:13px; }}
    .value {{ fill:#c9d1d9; font-size:13px; }}
    @keyframes print {{ to {{ opacity:1; transform:translateX(0); }} }}
    @media (prefers-reduced-motion:reduce) {{ .line {{ opacity:1; transform:none; animation:none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="489" height="351" rx="14" fill="#0d1117" stroke="#30363d" />
  <circle cx="22" cy="22" r="5" fill="#ff5f57" />
  <circle cx="39" cy="22" r="5" fill="#febc2e" />
  <circle cx="56" cy="22" r="5" fill="#28c840" />
  <text x="78" y="27" fill="#8b949e" font-size="12">dawood@github:~</text>
  <text x="30" y="63" fill="#56d364" font-size="14">$</text>
  <text x="48" y="63" fill="#f0f6fc" font-size="14" font-weight="700">neofetch --profile</text>
  <line x1="30" y1="76" x2="460" y2="76" stroke="#21262d" />
  {''.join(lines)}
  <rect x="30" y="327" width="8" height="15" fill="#56d364">{blink}</rect>
</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
