import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GRAPH_API = "https://graph.facebook.com/v21.0"

def post_to_facebook(message: str):
    """Post a text message to your Facebook Page."""
    url = f"{GRAPH_API}/{PAGE_ID}/feed"
    payload = {"message": message, "access_token": PAGE_TOKEN}

    response = requests.post(url, data=payload, timeout=30)
    if response.status_code == 200:
        print("✅ Post successful:", response.json())
    else:
        print("❌ Failed:", response.status_code, response.text)

if __name__ == "__main__":
    message = "📚 *Blair’s Whispers* — Dive into love, trust, and betrayal. Visit https://www.anitabestbooks.com 💕"
    post_to_facebook(message)
