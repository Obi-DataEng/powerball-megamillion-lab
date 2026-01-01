from pathlib import path
import json

out_dir = path("data/generated")
out_dir.mkdir(parents=True, exist_ok=True)

out_path = out_dir / f"daily_picks_{today}.json"
out_path.write_text(json.dumps(payload, indent=2), encoding = "utf-8")
print("Saved:", out_path)