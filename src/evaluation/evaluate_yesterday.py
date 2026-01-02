from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json


POWERBALL_DRAW_DAYS = {0, 2, 5}      # Mon, Wed, Sat
MEGAMILLIONS_DRAW_DAYS = {1, 4}     # Tue, Fri


def game_for_weekday(wd: int) -> str | None:
    if wd in POWERBALL_DRAW_DAYS:
        return "powerball"
    if wd in MEGAMILLIONS_DRAW_DAYS:
        return "megamillions"
    return None


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_draw_for_date(raw_draws: list[dict], iso_date: str) -> dict | None:
    """
    Finds the draw record matching date (YYYY-MM-DD) in your raw canonical JSON.
    Handles Powerball ISO timestamps and MegaMillions date strings.
    """
    for d in raw_draws:
        # powerball draw_date looks like "2025-12-24T00:00:00.000"
        # megamillions draw_date looks like "2006-10-17"
        draw_date = str(d.get("draw_date", ""))
        if draw_date.startswith(iso_date):
            return d
    return None


def score_line(white: list[int], bonus: int, winning_white: list[int], winning_bonus: int) -> dict:
    match_white = len(set(white) & set(winning_white))
    match_bonus = int(bonus == winning_bonus)
    return {"match_white": match_white, "match_bonus": match_bonus}


def main() -> None:
    now = datetime.now(timezone.utc)
    yesterday = (now.date() - timedelta(days=1))
    yday = yesterday.isoformat()

    yday_game = game_for_weekday(yesterday.weekday())
    reports_dir = Path("reports/daily")
    reports_dir.mkdir(parents=True, exist_ok=True)

    if yday_game is None:
        out = {
            "run_date": now.date().isoformat(),
            "yesterday_date": yday,
            "yesterday_game": None,
            "message": "No draw yesterday.",
        }
        out_path = reports_dir / f"evaluation_{yday}.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"[evaluate] {out['message']} Wrote -> {out_path}")
        return

    picks_path = Path("data/generated") / f"daily_picks_{yday}.json"
    if not picks_path.exists():
        out = {
            "run_date": now.date().isoformat(),
            "yesterday_date": yday,
            "yesterday_game": yday_game,
            "message": f"No picks file found for {yday}.",
        }
        out_path = reports_dir / f"evaluation_{yday}.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"[evaluate] {out['message']} Wrote -> {out_path}")
        return

    picks_payload = read_json(picks_path)
    game_lines = picks_payload["picks"][yday_game]

    # Load canonical raw draws
    raw_path = Path("data/raw") / ("powerball_draws.json" if yday_game == "powerball" else "megamillions_draws.json")
    raw_draws = read_json(raw_path)
    draw = latest_draw_for_date(raw_draws, yday)

    if draw is None:
        out = {
            "run_date": now.date().isoformat(),
            "yesterday_date": yday,
            "yesterday_game": yday_game,
            "message": f"No draw record found yet for {yday}. (Maybe data source not updated.)",
        }
        out_path = reports_dir / f"evaluation_{yday}.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"[evaluate] {out['message']} Wrote -> {out_path}")
        return

    winning_white = draw["white_numbers"]
    winning_bonus = draw["bonus_ball"]

    line_scores = []
    best = None
    for idx, line in enumerate(game_lines, start=1):
        s = score_line(line["white_balls"], line["bonus_ball"], winning_white, winning_bonus)
        row = {
            "line": idx,
            "white_balls": line["white_balls"],
            "bonus_ball": line["bonus_ball"],
            **s,
        }
        line_scores.append(row)
        # pick "best" as highest white matches, then bonus
        key = (row["match_white"], row["match_bonus"])
        if best is None or key > (best["match_white"], best["match_bonus"]):
            best = row

    out = {
        "run_date": now.date().isoformat(),
        "yesterday_date": yday,
        "yesterday_game": yday_game,
        "winning": {
            "white_numbers": winning_white,
            "bonus_ball": winning_bonus,
        },
        "results": line_scores,
        "best_line": best,
    }

    out_path = reports_dir / f"evaluation_{yday}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[evaluate] Wrote -> {out_path}")


if __name__ == "__main__":
    main()
