"""Fetch Dawood's public GitHub contribution calendar without an API token."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = os.getenv("GITHUB_PROFILE_USERNAME", "Dawood-code")
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "contributions.json"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"


def tooltip_count(text: str) -> int:
    match = re.search(r"([\d,]+) contribution", text)
    return int(match.group(1).replace(",", "")) if match else 0


def longest_streak(days: list[dict[str, object]]) -> int:
    longest = running = 0
    for day in days:
        if int(day["count"]) > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    return longest


def current_streak(days: list[dict[str, object]]) -> int:
    if not days:
        return 0

    active_dates = [date.fromisoformat(str(day["date"])) for day in days if int(day["count"]) > 0]
    if not active_dates:
        return 0

    end = date.fromisoformat(str(days[-1]["date"]))
    most_recent = active_dates[-1]
    if (end - most_recent).days > 1:
        return 0

    active = set(active_dates)
    streak = 0
    cursor = most_recent
    while cursor in active:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def fetch() -> dict[str, object]:
    response = requests.get(
        CONTRIBUTIONS_URL,
        headers={
            "Accept": "text/html",
            "User-Agent": f"{USERNAME}-profile-readme/1.0",
        },
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    days: list[dict[str, object]] = []
    for cell in soup.select("[data-date][data-level]"):
        cell_id = cell.get("id")
        tooltip = soup.find("tool-tip", attrs={"for": cell_id}) if cell_id else None
        count = tooltip_count(tooltip.get_text(" ", strip=True)) if tooltip else 0
        days.append(
            {
                "date": str(cell["data-date"]),
                "count": count,
                "level": int(str(cell.get("data-level", "0"))),
            }
        )

    days.sort(key=lambda item: str(item["date"]))
    if not days:
        raise RuntimeError("GitHub returned no contribution days; its calendar markup may have changed.")

    total = sum(int(day["count"]) for day in days)
    best = max(days, key=lambda item: int(item["count"]))
    months: dict[str, int] = {}
    for day in days:
        month = str(day["date"])[:7]
        months[month] = months.get(month, 0) + int(day["count"])

    return {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total": total,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly_totals": months,
        "days": days,
    }


def main() -> None:
    payload = fetch()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['days'])} days and {payload['total']} contributions to {OUTPUT}")


if __name__ == "__main__":
    main()
