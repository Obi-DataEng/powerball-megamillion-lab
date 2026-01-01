from pathlib import Path
import json

gen_dir = Path("data/generated")
rep_dir = Path("reports/daily")
rep_dir.mkdir(parents=True, exist_ok=True)

picks_path = gen_dir / f"daily_picks_{yesterday}.json"
if not picks_path.exists():
    print(f"No picks found for {yesterday} - skipping evaluation.")
    return

picks = json.loads(picks_path.read_text(encoding="utf-8"))["lines"]

out = rep_dir / f"report_{yesterday}.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Saved report:", out)
