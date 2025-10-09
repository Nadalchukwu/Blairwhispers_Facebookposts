import os
import datetime
import pathlib
import requests
from dotenv import load_dotenv

load_dotenv()
PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GRAPH = "https://graph.facebook.com/v21.0"
DEFAULT_TAGS = ["#BlairsWhispers", "#Romance", "#BookLovers"]

def pick_message(path="posts.txt") -> str:
    p = pathlib.Path(path)
    if not p.exists():
        return "✨ Blair’s Whispers — New chapter tease today! https://www.anitabestbooks.com #BlairsWhispers #Romance"
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return "✨ Blair’s Whispers — New chapter tease today! https://www.anitabestbooks.com #BlairsWhispers #Romance"
    idx = datetime.date.today().toordinal() % len(lines)
    msg = lines[idx]
    # Light touch: ensure at least one default tag exists
    if not any(tag.lower() in msg.lower() for tag in DEFAULT_TAGS):
        msg = msg.rstrip() + " " + " ".join(DEFAULT_TAGS[:2])
    return msg

def post_text(message: str) -> str:
    url = f"{GRAPH}/{PAGE_ID}/feed"
    data = {"message": message, "access_token": PAGE_TOKEN}
    r = requests.post(url, data=data, timeout=30)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        print("❌ Failed:", r.status_code, r.text)
        raise
    res = r.json()
    print("✅ Post successful:", res)
    return res.get("id", "")

if __name__ == "__main__":
    msg = pick_message()
    post_text(msg)
