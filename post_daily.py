import os, sys, datetime, pathlib, requests, smtplib, ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GRAPH = "https://graph.facebook.com/v21.0"

# ---- controls ----
START_DATE = os.getenv("START_DATE")         # e.g., "2025-10-09"
MAX_DAYS = int(os.getenv("MAX_DAYS", "20"))  # number of days to post

# ---- email (SMTP) config via env/secrets ----
SMTP_HOST = os.getenv("SMTP_HOST")           # e.g., smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")           # your email address
SMTP_PASS = os.getenv("SMTP_PASS")           # app password (Gmail) / account password (provider)
EMAIL_TO  = os.getenv("EMAIL_TO", SMTP_USER) # where to send
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

def send_email(subject: str, body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("Email not configured; skipping.")
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls(context=ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    print(f"📧 Sent email to {EMAIL_TO}")

def pick_message(index: int, path="posts.txt") -> str:
    lines = [ln.strip() for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if index >= len(lines):
        print("No unused lines left in posts.txt; skipping."); sys.exit(0)
    msg = lines[index]
    # ensure at least one brand tag present
    if "#blairswhispers" not in msg.lower():
        msg = msg.rstrip() + " #BlairsWhispers #Romance"
    return msg

def post_text(message: str) -> str:
    r = requests.post(f"{GRAPH}/{PAGE_ID}/feed",
                      data={"message": message, "access_token": PAGE_TOKEN},
                      timeout=30)
    r.raise_for_status()
    res = r.json()
    print("✅ Post successful:", res)
    return res.get("id", "")

if __name__ == "__main__":
    if not START_DATE:
        print("START_DATE not set; skipping."); sys.exit(0)
    start = datetime.date.fromisoformat(START_DATE)
    today = datetime.date.today()
    day_index = (today - start).days

    if day_index < 0:
        print(f"Not started yet (starts {start})."); sys.exit(0)

    # Post on days 0..MAX_DAYS-1
    if 0 <= day_index < MAX_DAYS:
        post_text(pick_message(day_index))
        sys.exit(0)

    # Send ONE email on the first day AFTER the last post (day_index == MAX_DAYS)
    if day_index == MAX_DAYS:
        last_post_date = start + datetime.timedelta(days=MAX_DAYS - 1)
        subject = f"Blair’s Whispers: daily posts completed ({MAX_DAYS}/{MAX_DAYS})"
        body = (
            f"Hi,\n\nYour scheduled Facebook Page posts have finished.\n\n"
            f"Start date: {start}\n"
            f"Last post:  {last_post_date}\n"
            f"Page ID:    {PAGE_ID}\n\n"
            f"You can disable the workflow or extend MAX_DAYS/add more lines to posts.txt.\n"
        )
        send_email(subject, body)
        print("Done. Completion email sent.")
        sys.exit(0)

    # After MAX_DAYS, do nothing (no repeated emails)
    print("Completed previously; no action today.")
