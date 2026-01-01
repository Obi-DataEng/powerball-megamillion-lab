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
    today = datetime.utcnow().date().isoformat()
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()

    picks = load_json(Path(f"data/generated/daily_picks_{today}.json"))
    evaluation = load_json(Path(f"reports/daily/report_{yesterday}.json"))

    lines = []
    lines.append(f"🎯 Daily Lottery Picks ({today})\n")

    if picks:
        for line in picks["lines"]:
            lines.append(
                f"{line['game'].upper()}: "
                f"{', '.join(map(str, line['white_balls']))} + {line['bonus_ball']}"
            )
    else:
        lines.append("No picks generated today.")

    lines.append("\n📊 Yesterday's Results\n")

    if evaluation:
        lines.append(
            f"Wins: {evaluation['total_wins']}\n"
            f"Estimated payout: ${evaluation['estimated_payout']}"
        )
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
