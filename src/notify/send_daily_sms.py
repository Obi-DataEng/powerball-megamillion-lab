from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import json
import os
from twilio.rest import Client

GEN_DIR = Path("data/generated")
REP_DIR = Path("reports/daily")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def format_lines(picks: dict) -> str:
    # Keep SMS short: show 1 line per game (first occurrence)
    pb = next((l for l in picks["lines"] if l.get("game") == "powerball"), None)
    mm = next((l for l in picks["lines"] if l.get("game") == "megamillions"), None)

    parts = []
    if pb:
        whites = "-".join(map(str, pb["white_numbers"]))
        parts.append(f"PB {whites} + {pb['bonus_ball']}")
    if mm:
        whites = "-".join(map(str, mm["white_numbers"]))
        parts.append(f"MM {whites} + {mm['bonus_ball']}")
    return " | ".join(parts)

def format_eval(report: dict | None) -> str:
    if not report:
        return "Yday: no eval yet"
    t = report.get("totals", {})
    return f"Yday wins: {t.get('winning_lines', 0)}, est: {t.get('total_estimated_winnings_label', '$0')}"

def send_sms(body: str):
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    msg = client.messages.create(
        body=body,
        from_=os.environ["TWILIO_FROM_NUMBER"],
        to=os.environ["TWILIO_TO_NUMBER"],
    )
    print(f"SMS sent: sid={msg.sid}")

def main():
    today = datetime.utcnow().date().isoformat()
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()

    picks_path = GEN_DIR / f"daily_picks_{today}.json"
    report_path = REP_DIR / f"report_{yesterday}.json"

    if not picks_path.exists():
        print("No picks found for today — skipping SMS.")
        return

    picks = load_json(picks_path)
    report = load_json(report_path) if report_path.exists() else None

    picks_text = format_lines(picks)
    eval_text = format_eval(report)

    # SMS body (keep it under ~160-300 chars ideally)
    body = f"🎯 {today} Picks: {picks_text}\n📊 {eval_text}"
    send_sms(body)

if __name__ == "__main__":
    main()
