import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta

def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())

def build_email_body():
    from datetime import datetime, timedelta, UTC

    today = datetime.now(UTC).date().isoformat()
    yesterday = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()

    picks = load_json(Path(f"data/generated/daily_picks_{today}.json"))
    evaluation = load_json(Path(f"reports/daily/report_{yesterday}.json"))

    lines = []
    lines.append(f"🎯 Daily Lottery Picks ({today})\n")

    if picks and picks.get("lines"):
        for line in picks["lines"]:
            game = (line.get("game") or "game").upper()

            # Accept multiple possible field names
            whites = (
                line.get("white_balls")
                or line.get("white_numbers")
                or line.get("numbers")
                or []
            )

            bonus = (
                line.get("bonus_ball")
                or line.get("powerball")
                or line.get("mega_ball")
                or line.get("bonus")
                or "?"
            )

            lines.append(f"{game}: {', '.join(map(str, whites))} + {bonus}")
    else:
        lines.append("No picks generated today.")

    lines.append("\n📊 Yesterday's Results\n")

    if evaluation:
        lines.append(f"Wins: {evaluation.get('total_wins', 0)}")
        lines.append(f"Estimated payout: ${evaluation.get('estimated_payout', 0)}")
    else:
        lines.append("No evaluation available.")

    return "\n".join(lines)


def send_email(body: str):
    host = os.environ["EMAIL_HOST"]
    port = int(os.environ["EMAIL_PORT"])
    user = os.environ["EMAIL_USERNAME"]
    password = os.environ["EMAIL_PASSWORD"]
    to_email = os.environ["EMAIL_TO"]

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to_email
    msg["Subject"] = "🎰 Daily Lottery Picks + Results"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

    print("Email sent successfully.")

def main():
    body = build_email_body()
    send_email(body)

if __name__ == "__main__":
    main()
