from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import random


@dataclass(frozen=True)
class GameRules:
    name: str
    white_min: int
    white_max: int
    white_count: int
    bonus_min: int
    bonus_max: int
    bonus_name: str


POWERBALL = GameRules(
    name="powerball",
    white_min=1, white_max=69, white_count=5,
    bonus_min=1, bonus_max=26, bonus_name="powerball",
)

MEGAMILLIONS = GameRules(
    name="megamillions",
    white_min=1, white_max=70, white_count=5,
    bonus_min=1, bonus_max=25, bonus_name="mega_ball",
)


def make_line(rules: GameRules) -> dict:
    whites = sorted(random.sample(range(rules.white_min, rules.white_max + 1), rules.white_count))
    bonus = random.randint(rules.bonus_min, rules.bonus_max)
    return {
        "white_balls": whites,
        "bonus_ball": bonus,
        "bonus_name": rules.bonus_name,
    }


def main() -> None:
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()

    # Approach A: always generate both games daily
    lines_per_game = 5
    payload = {
        "run_date": today,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "picks": {
            "powerball": [make_line(POWERBALL) for _ in range(lines_per_game)],
            "megamillions": [make_line(MEGAMILLIONS) for _ in range(lines_per_game)],
        },
        "meta": {
            "lines_per_game": lines_per_game,
            "version": "1.0",
        }
    }

    out_dir = Path("data/generated")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"daily_picks_{today}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved daily picks -> {out_path}")


if __name__ == "__main__":
    main()