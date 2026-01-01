from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, date
import json
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------
# Paths
# -----------------------------
GEN_DIR = Path("data/generated")
RAW_DIR = Path("data/raw")
REPORT_DIR = Path("reports/daily")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Prize tables (base prizes, no multipliers)
# Amounts are in USD.
# Keys are (white_matches, bonus_match_bool)
# -----------------------------

POWERBALL_PRIZES = {
    (5, True): "JACKPOT",
    (5, False): 1_000_000,
    (4, True): 50_000,
    (4, False): 100,
    (3, True): 100,
    (3, False): 7,
    (2, True): 7,
    (1, True): 4,
    (0, True): 4,
}

MEGAMILLIONS_PRIZES = {
    (5, True): "JACKPOT",
    (5, False): 1_000_000,
    (4, True): 10_000,
    (4, False): 500,
    (3, True): 200,
    (3, False): 10,
    (2, True): 10,
    (1, True): 4,
    (0, True): 2,
}


# -----------------------------
# Utilities
# -----------------------------

def iso_yesterday_utc() -> str:
    """Yesterday's date in UTC as YYYY-MM-DD."""
    y = (datetime.utcnow().date() - timedelta(days=1))
    return y.isoformat()


def parse_date_any(s: str) -> Optional[date]:
    """
    Parse draw_date formats we might see:
    - '2025-12-23T00:00:00.000'
    - '2025-12-23'
    """
    if not s:
        return None
    try:
        # Handles ISO timestamps like 2025-12-23T00:00:00.000
        return datetime.fromisoformat(s.replace("Z", "")).date()
    except ValueError:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def normalize_whites(value: Any) -> List[int]:
    """
    Accepts whites as:
    - list[int] (already parsed)
    - '1 2 3 4 5' (space-separated)
    - '01 02 03 04 05' etc.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [int(x) for x in value]
    if isinstance(value, str):
        parts = value.replace(",", " ").split()
        return [int(p) for p in parts if p.strip().isdigit()]
    return []


def normalize_bonus(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_draw_for_date(draws: List[Dict[str, Any]], target: date) -> Optional[Dict[str, Any]]:
    """
    Your ingestion outputs are already canonical, but we keep this flexible.
    We look for a record whose draw_date matches target date.
    """
    for r in draws:
        d = parse_date_any(str(r.get("draw_date", "")))
        if d == target:
            return r
    return None


def score_line(
    picked_whites: List[int],
    picked_bonus: int,
    win_whites: List[int],
    win_bonus: int,
) -> Tuple[int, bool]:
    white_matches = len(set(picked_whites) & set(win_whites))
    bonus_match = (picked_bonus == win_bonus)
    return white_matches, bonus_match


def prize_for(game: str, white_matches: int, bonus_match: bool):
    if game == "powerball":
        return POWERBALL_PRIZES.get((white_matches, bonus_match), 0)
    if game == "megamillions":
        return MEGAMILLIONS_PRIZES.get((white_matches, bonus_match), 0)
    return 0


def dollars(prize) -> int:
    return 0 if prize == "JACKPOT" else int(prize)


# -----------------------------
# Main evaluation
# -----------------------------

def main() -> None:
    yesterday_iso = iso_yesterday_utc()
    yesterday_dt = datetime.strptime(yesterday_iso, "%Y-%m-%d").date()

    picks_path = GEN_DIR / f"daily_picks_{yesterday_iso}.json"
    if not picks_path.exists():
        print(f"[evaluate] No picks found for {yesterday_iso} at {picks_path}. Skipping.")
        return

    # Load picks payload
    picks_payload = load_json(picks_path)
    lines = picks_payload.get("lines", [])
    if not isinstance(lines, list) or not lines:
        print(f"[evaluate] Picks file exists but contains no lines. Skipping.")
        return

    # Load draws
    pb_path = RAW_DIR / "powerball_draws.json"
    mm_path = RAW_DIR / "megamillions_draws.json"

    if not pb_path.exists() or not mm_path.exists():
        print("[evaluate] Missing draw files in data/raw. Run ingestion first. Skipping.")
        return

    pb_draws = load_json(pb_path)
    mm_draws = load_json(mm_path)

    # Find yesterday’s draw records
    pb_draw = find_draw_for_date(pb_draws, yesterday_dt) if isinstance(pb_draws, list) else None
    mm_draw = find_draw_for_date(mm_draws, yesterday_dt) if isinstance(mm_draws, list) else None

    # If one game didn't draw yesterday (or data not present), we still evaluate what we can.
    winning: Dict[str, Any] = {}

    if pb_draw:
        winning["powerball"] = {
            "draw_date": str(pb_draw.get("draw_date")),
            "white_numbers": normalize_whites(pb_draw.get("white_numbers")),
            "bonus_ball": normalize_bonus(pb_draw.get("bonus_ball")),
        }

    if mm_draw:
        winning["megamillions"] = {
            "draw_date": str(mm_draw.get("draw_date")),
            "white_numbers": normalize_whites(mm_draw.get("white_numbers")),
            "bonus_ball": normalize_bonus(mm_draw.get("bonus_ball")),
        }

    if not winning:
        print(f"[evaluate] No matching draws found for {yesterday_iso}. Skipping.")
        return

    # Evaluate lines
    evaluated: List[Dict[str, Any]] = []
    totals = {
        "total_lines": 0,
        "powerball_lines": 0,
        "megamillions_lines": 0,
        "winning_lines": 0,
        "jackpot_hits": 0,
        "total_estimated_winnings": 0,
    }

    best = {
        "prize": 0,
        "prize_label": "$0",
        "line": None,
    }

    for i, line in enumerate(lines, start=1):
        game = line.get("game")
        if game not in ("powerball", "megamillions"):
            continue

        # If we don't have winning numbers for that game/date, skip evaluation for that line
        if game not in winning:
            continue

        picked_whites = normalize_whites(line.get("white_numbers"))
        picked_bonus = normalize_bonus(line.get("bonus_ball"))
        if picked_bonus is None:
            continue

        win_whites = winning[game]["white_numbers"]
        win_bonus = winning[game]["bonus_ball"]
        if win_bonus is None:
            continue

        white_matches, bonus_match = score_line(picked_whites, picked_bonus, win_whites, win_bonus)
        prize = prize_for(game, white_matches, bonus_match)

        is_winner = (prize != 0)
        is_jackpot = (prize == "JACKPOT")

        prize_label = "JACKPOT" if is_jackpot else f"${int(prize):,}"

        evaluated_line = {
            "line_id": i,
            "game": game,
            "picked_white_numbers": picked_whites,
            "picked_bonus_ball": picked_bonus,
            "winning_white_numbers": win_whites,
            "winning_bonus_ball": win_bonus,
            "white_matches": white_matches,
            "bonus_match": bool(bonus_match),
            "prize": prize,
            "prize_label": prize_label,
            "strategy": line.get("strategy", "unknown"),
        }
        evaluated.append(evaluated_line)

        # Totals
        totals["total_lines"] += 1
        if game == "powerball":
            totals["powerball_lines"] += 1
        else:
            totals["megamillions_lines"] += 1

        if is_winner:
            totals["winning_lines"] += 1
        if is_jackpot:
            totals["jackpot_hits"] += 1

        totals["total_estimated_winnings"] += dollars(prize)

        # Best line
        best_value = float("inf") if is_jackpot else dollars(prize)
        current_best = float("inf") if best["prize_label"] == "JACKPOT" else int(best["prize"])
        if best["line"] is None or best_value > current_best:
            best["prize"] = 0 if is_jackpot else dollars(prize)
            best["prize_label"] = "JACKPOT" if is_jackpot else f"${dollars(prize):,}"
            best["line"] = evaluated_line

    # Build report
    report: Dict[str, Any] = {
        "evaluated_for_date": yesterday_iso,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "picks_source": str(picks_path),
        "winning_draws_used": winning,
        "totals": {
            **totals,
            "total_estimated_winnings_label": f"${totals['total_estimated_winnings']:,}",
        },
        "best_line": best,
        "lines": evaluated,
        "notes": [
            "Prizes are estimated using base prize tiers (no Power Play / Megaplier).",
            "If a draw for a game/date wasn't found, lines for that game are skipped.",
        ],
    }

    out_path = REPORT_DIR / f"report_{yesterday_iso}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[evaluate] Evaluated date: {yesterday_iso}")
    print(f"[evaluate] Total lines scored: {totals['total_lines']}")
    print(f"[evaluate] Winning lines: {totals['winning_lines']}")
    print(f"[evaluate] Total estimated winnings: ${totals['total_estimated_winnings']:,}")
    print(f"[evaluate] Saved report -> {out_path}")


if __name__ == "__main__":
    main()
