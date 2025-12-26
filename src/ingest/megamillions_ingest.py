from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import requests

MEGAMILLIONS_URL = "https://data.ny.gov/resource/5xaw-6ayf.json"
RAW_DIR = Path("data/raw")
CANONICAL_OUT = RAW_DIR / "megamillions_draws.json"
SOURCE_SNAPSHOT_OUT = RAW_DIR / "megamillions_source_snapshot.json"

def fetch_json(url: str, params: dict | None = None, timeout_seconds: int = 20) -> Any:
    resp = requests.get(
        url,
        params=params,
        timeout=timeout_seconds,
        headers={"User-Agent": "powerball-megamillion-lab/1.0"},
    )

    if resp.status_code != 200:
        print("Status:", resp.status_code)
        print("URL:", resp.url)
        print("Preview:", resp.text[:300])
        resp.raise_for_status()

    data = resp.json()
    if data is None:
        raise ValueError(f"API returned JSON null. URL={resp.url}")

    return data

def parse_draw_date(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        return value[:10]

def normalize_megamillions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ingested_at = datetime.now(timezone.utc).isoformat()
    out: List[Dict[str, Any]] = []
    skipped = 0

    for r in rows:
        try:
            draw_date = parse_draw_date(str(r["draw_date"]))

            whites = [int(x) for x in str(r["winning_numbers"]).split()]
            if len(whites) != 5:
                skipped += 1
                continue

            mega_ball = int(r["mega_ball"])

            out.append(
                {
                    "game": "megamillions",
                    "draw_date": draw_date,
                    "white_numbers": whites,
                    "bonus_ball": mega_ball,   # we use bonus_ball generically
                    "multiplier": r.get("multiplier"),  # optional, may be missing
                    "source": "data.ny.gov",
                    "ingested_at": ingested_at,
                }
            )
        except Exception:
            skipped += 1
            continue

    print(f"Normalized {len(out)} records; skipped {skipped} malformed rows.")
    return out

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def main() -> None:
    # NOTE: In PowerShell, $ has special meaning, but here it's inside Python so it's fine.
    payload = fetch_json(
        MEGAMILLIONS_URL,
        params={"$limit": 2000, "$order": "draw_date DESC"},
    )

    write_json(SOURCE_SNAPSHOT_OUT, payload)

    records = normalize_megamillions(payload)
    write_json(CANONICAL_OUT, records)

    if records:
        dates = sorted(r["draw_date"] for r in records)
        print(f"Fetched {len(records)} Mega Millions draws")
        print(f"Date range: {dates[0]} → {dates[-1]}")
        print(f"Saved canonical: {CANONICAL_OUT}")
        print(f"Saved snapshot : {SOURCE_SNAPSHOT_OUT}")
    else:
        print("No Mega Millions records were written. Check the source payload format.")


if __name__ == "__main__":
    main()

