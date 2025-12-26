from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests


POWERBALL_URL = "https://data.ny.gov/resource/d6yy-54nr.json"

RAW_DIR = Path("data/raw")
CANONICAL_OUT = RAW_DIR / "powerball_draws.json"
SOURCE_SNAPSHOT_OUT = RAW_DIR / "powerball_source_snapshot.json"

def fetch_json(url: str, params: dict | None = None, timeout_seconds: int = 20):
    resp = requests.get(
        url,
        params=params,
        timeout=timeout_seconds,
        headers={"User-Agent": "powerball-megamillions-lab/1.0"},
    )

    # Helpful debugging if anything goes sideways
    if resp.status_code != 200:
        print("Status:", resp.status_code)
        print("URL:", resp.url)
        print("Preview:", resp.text[:300])
        resp.raise_for_status()

    data = resp.json()

    if data is None:
        raise ValueError(f"API returned JSON null. URL={resp.url}")

    return data

payload = fetch_json(
    POWERBALL_URL,
    params={"$limit": 2000, "$order": "draw_date DESC"},
)

def parse_draw_date(value: str) -> str:
    """
    Normalize draw_date to YYYY-MM-DD (string) for consistent downstream use.
    Powerball typically returns YYYY-MM-DD.
    """
    # Keep it robust in case format changes.
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        # As fallback, trust first 10 chars if it looks like a date.
        return value[:10]


def normalize_powerball(rows: list[dict]) -> list[dict]:
    ingested_at = datetime.now(timezone.utc).isoformat()
    out = []

    for r in rows:
        draw_date = r["draw_date"]  # already ISO-ish
        nums = [int(x) for x in r["winning_numbers"].split()]

        whites = nums[:5]
        powerball = nums[5]

        out.append({
            "game": "powerball",
            "draw_date": draw_date,
            "white_numbers": whites,
            "bonus_ball": powerball,
            "multiplier": r.get("multiplier"),
            "source": "data.ny.gov",
            "ingested_at": ingested_at,
        })

    return out



def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def main() -> None:
    payload = fetch_json(POWERBALL_URL)

    # Save a source snapshot for audit/debugging (optional but very useful)
    write_json(SOURCE_SNAPSHOT_OUT, payload)

    records = normalize_powerball(payload)
    write_json(CANONICAL_OUT, records)

    if records:
        dates = sorted(r["draw_date"] for r in records)
        print(f"Fetched {len(records)} Powerball draws")
        print(f"Date range: {dates[0]} → {dates[-1]}")
        print(f"Saved canonical: {CANONICAL_OUT}")
        print(f"Saved snapshot : {SOURCE_SNAPSHOT_OUT}")
    else:
        print("No Powerball records were written. Check the source payload format.")


if __name__ == "__main__":
    main()
