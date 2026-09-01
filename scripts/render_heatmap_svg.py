"""Render the saved contribution data as a self-contained animated SVG."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contrib-heatmap.svg"

WIDTH = 860
HEIGHT = 250
CELL = 11
GAP = 3
STEP = CELL + GAP
GRID_X = 94
GRID_Y = 69
PALETTE = ["#21262d", "#0e4429", "#006d32", "#26a641", "#56d364"]


def plural(value: int, noun: str) -> str:
    return f"{value:,} {noun}{'' if value == 1 else 's'}"


def sunday_index(value: date) -> int:
    return (value.weekday() + 1) % 7


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    days = {date.fromisoformat(day["date"]): day for day in payload["days"]}
    first = min(days)
    last = max(days)
    grid_start = first - timedelta(days=sunday_index(first))
    grid_end = last + timedelta(days=6 - sunday_index(last))
    weeks = ((grid_end - grid_start).days + 1) // 7

    cells: list[str] = []
    cursor = grid_start
    while cursor <= grid_end:
        col = (cursor - grid_start).days // 7
        row = sunday_index(cursor)
        day = days.get(cursor, {"count": 0, "level": 0})
        level = max(0, min(int(day["level"]), len(PALETTE) - 1))
        x = GRID_X + col * STEP
        y = GRID_Y + row * STEP
        delay = (col + row) * 0.018
        label = f"{cursor.isoformat()}: {plural(int(day['count']), 'contribution')}"
        cells.append(
            f'<rect class="day" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
            f"<title>{escape(label)}</title></rect>"
        )
        cursor += timedelta(days=1)

    month_labels: list[str] = []
    last_labeled_col = -10
    cursor = first.replace(day=1)
    if cursor < first:
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    while cursor <= last:
        col = (cursor - grid_start).days // 7
        if col - last_labeled_col >= 3:
            x = GRID_X + col * STEP
            month_labels.append(f'<text class="month" x="{x}" y="55">{cursor.strftime("%b")}</text>')
            last_labeled_col = col
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    total = int(payload["total"])
    current = int(payload["current_streak"])
    longest = int(payload["longest_streak"])
    best = payload["best_day"]
    best_text = "No active day yet"
    if int(best["count"]) > 0:
        best_month = datetime.strptime(best["date"], "%Y-%m-%d").strftime("%b")
        best_text = f"{best_month} {int(best['date'][-2:])} · {plural(int(best['count']), 'contribution')}"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(str(payload['username']))}'s contribution calendar</title>
  <desc id="desc">{plural(total, 'contribution')} in the last year, animated week by week.</desc>
  <style>
    .shell {{ fill:#0d1117; stroke:#30363d; stroke-width:1; }}
    text {{ font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace; }}
    .title {{ fill:#f0f6fc; font-size:17px; font-weight:700; }}
    .sub {{ fill:#8b949e; font-size:12px; }}
    .month,.weekday {{ fill:#8b949e; font-size:10px; }}
    .stat-label {{ fill:#8b949e; font-size:11px; }}
    .stat-value {{ fill:#c9d1d9; font-size:12px; font-weight:600; }}
    .day {{ opacity:0; transform:translateY(-8px); animation:reveal .42s cubic-bezier(.2,.8,.2,1) forwards; }}
    @keyframes reveal {{ to {{ opacity:1; transform:translateY(0); }} }}
    @media (prefers-reduced-motion:reduce) {{ .day {{ opacity:1; transform:none; animation:none; }} }}
  </style>
  <rect class="shell" x="0.5" y="0.5" width="859" height="249" rx="14" />
  <circle cx="22" cy="22" r="5" fill="#ff5f57" />
  <circle cx="39" cy="22" r="5" fill="#febc2e" />
  <circle cx="56" cy="22" r="5" fill="#28c840" />
  <text class="title" x="78" y="28">./contributions.sh</text>
  <text class="sub" x="836" y="27" text-anchor="end">updated {escape(str(payload['range']['end']))}</text>
  {''.join(month_labels)}
  <text class="weekday" x="25" y="91">Mon</text>
  <text class="weekday" x="25" y="119">Wed</text>
  <text class="weekday" x="25" y="147">Fri</text>
  {''.join(cells)}
  <line x1="24" y1="181" x2="836" y2="181" stroke="#21262d" />
  <text class="stat-label" x="25" y="207">LAST YEAR</text>
  <text class="stat-value" x="25" y="227">{plural(total, 'contribution')}</text>
  <text class="stat-label" x="245" y="207">CURRENT STREAK</text>
  <text class="stat-value" x="245" y="227">{plural(current, 'day')}</text>
  <text class="stat-label" x="445" y="207">LONGEST STREAK</text>
  <text class="stat-value" x="445" y="227">{plural(longest, 'day')}</text>
  <text class="stat-label" x="635" y="207">BEST DAY</text>
  <text class="stat-value" x="635" y="227">{escape(best_text)}</text>
</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {weeks} weeks to {OUTPUT}")


if __name__ == "__main__":
    main()
