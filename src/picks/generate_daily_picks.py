from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import random
from typing import List, Dict, Any


# ---------- Helpers (pick logic) ----------

def sample_unique(rng: random.Random, low: int, high: int, k: int) -> List[int]:
    """Sample k unique integers in [low, high], sorted."""
    return sorted(rng.sample(range(low, high + 1), k))


def generate_powerball_line(rng: random.Random) -> Dict[str, Any]:
    """
    Powerball: pick 5 unique white balls from 1-69 + 1 Powerball from 1-26.
    """
    whites = sample_unique(rng, 1, 69, 5)
    bonus = rng.randint(1, 26)
    return {
        "game": "powerball",
        "white_numbers": whites,
        "bonus_ball": bonus,
        "strategy": "baseline_random",
    }


def generate_megamillions_line(rng: random.Random) -> Dict[str, Any]:
    """
    Mega Millions: pick 5 unique white balls from 1-70 + 1 Mega Ball from 1-25.
    """
    whites = sample_unique(rng, 1, 70, 5)
    bonus = rng.randint(1, 25)
    return {
        "game": "megamillions",
        "white_numbers": whites,
        "bonus_ball": bonus,
        "strategy": "baseline_random",
    }


# ---------- Main ----------

def main(lines_per_game: int = 5, seed: int | None = None) -> Path:
    """
    Generates daily picks for both games and saves to data/generated/ as JSON.

    Output file:
      data/generated/daily_picks_YYYY-MM-DD.json
    """
    # Use UTC so GitHub Actions runs are consistent regardless of runner timezone.
    today = datetime.utcnow().date().isoformat()

    rng = random.Random(seed)

    payload: Dict[str, Any] = {
        "run_date": today,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "lines_per_game": lines_per_game,
        "seed": seed,
        "lines": []
    }

    # Generate N lines per game
    for _ in range(lines_per_game):
        payload["lines"].append(generate_powerball_line(rng))
        payload["lines"].append(generate_megamillions_line(rng))

    out_dir = Path("data/generated")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"daily_picks_{today}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Generated {lines_per_game} lines per game ({2 * lines_per_game} total lines).")
    print(f"Saved daily picks -> {out_path}")

    return out_path


if __name__ == "__main__":
    main()