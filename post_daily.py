import os, sys, datetime, pathlib, requests
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageColor

# ===============================
# Config / Defaults
# ===============================
IMG_W, IMG_H = 1200, 630   # FB-friendly size
MARGIN       = 80          # px margin
LINE_SPACING = 12          # line spacing
FONT_SIZE    = 78          # base font size

# ===============================
# Helper: validate hex color strings
# ===============================
def safe_color(value: str, fallback: str) -> str:
    """Return a valid color string or the fallback if invalid."""
    try:
        ImageColor.getrgb(value)
        return value
    except Exception:
        return fallback

# ===============================
# Time guard (Toronto 10:00)
# ===============================
now_toronto = datetime.datetime.now(ZoneInfo("America/Toronto"))
if now_toronto.hour != 10:
    print(f"Skipping run: local time is {now_toronto:%Y-%m-%d %H:%M}, not 10:00.")
    sys.exit(0)

# =========================
# Env / Vars
# =========================
load_dotenv()

PAGE_ID    = os.getenv("FB_PAGE_ID")
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GRAPH      = "https://graph.facebook.com/v21.0"

# NOTE: default kept to 2025-11-02. Change here or via repository vars.
START_DATE = os.getenv("START_DATE", "2025-11-02")
if not START_DATE:
    print("START_DATE is not set; exiting.")
    sys.exit(0)

MAX_DAYS   = int(os.getenv("MAX_DAYS", "20"))
POSTS_FILE = os.getenv("POSTS_FILE", "posts.txt")
FONT_PATH  = os.getenv("FONT_PATH", "assets/font.ttf")

BG_COLOR   = safe_color(os.getenv("BG_COLOR", "#b900ff"), "#b900ff")
TEXT_COLOR = safe_color(os.getenv("TEXT_COLOR", "#FFFFFF"), "#FFFFFF")

# =========================
# Helpers
# =========================
def day_index() -> int:
    start = datetime.date.fromisoformat(START_DATE)
    return (now_toronto.date() - start).days

def read_message(idx: int) -> str:
    p = pathlib.Path(POSTS_FILE)
    if not p.exists():
        print(f"Posts file not found at {p.resolve()}")
        sys.exit(0)
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print("Posts file is empty.")
        sys.exit(0)
    if idx < 0 or idx >= min(len(lines), MAX_DAYS):
        print(f"Done or out of range: idx={idx}, lines={len(lines)}, MAX_DAYS={MAX_DAYS}")
        sys.exit(0)
    return lines[idx]

def render_image(text: str, out_path: str) -> None:
    # Load font with fallback
    try:
        font = ImageFont.truetype(FONT_PATH, size=FONT_SIZE)
    except Exception as e:
        print(f"Could not load font at {FONT_PATH}: {e}. Using default font.")
        font = ImageFont.load_default()

    img  = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    max_width = IMG_W - 2 * MARGIN
    wrapped = []

    # simple wrapping by measuring each candidate line
    for para in text.split("\n"):
        if not para:
            wrapped.append("")  # preserve blank lines
            continue
        line = ""
        for word in para.split():
            test = (line + " " + word).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                line = test
            else:
                if line:
                    wrapped.append(line)
                line = word
        if line:
            wrapped.append(line)

    # compute total text height
    line_heights = []
    for ln in wrapped:
        bbox = draw.textbbox((0, 0), ln if ln else " ", font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
    total_h = sum(line_heights) + (len(wrapped) - 1) * LINE_SPACING

    # vertical centering (clamp to MARGIN)
    y = max((IMG_H - total_h) // 2, MARGIN)

    # draw centered
    for ln, h in zip(wrapped, line_heights):
        display_text = ln if ln else " "
        bbox = draw.textbbox((0, 0), display_text, font=font)
        w = bbox[2] - bbox[0]
        x = (IMG_W - w) // 2
        draw.text((x, y), display_text, font=font, fill=TEXT_COLOR)
        y += h + LINE_SPACING

    img.save(out_path, format="PNG")

def post_photo(photo_path: str, caption: str) -> None:
    with open(photo_path, "rb") as f:
        data = {
            "caption": caption,
            "access_token": PAGE_TOKEN,
            "published": "true",
        }
        r = requests.post(
            f"{GRAPH}/{PAGE_ID}/photos",
            data=data,
            files={"source": f},
            timeout=120
        )
    r.raise_for_status()
    print("Photo post OK:", r.json())

# =========================
# Main
# =========================
if __name__ == "__main__":
    idx = day_index()
    message = read_message(idx)
    out_name = f"out_{now_toronto:%Y%m%d}_{idx+1}.png"
    render_image(message, out_name)
    post_photo(out_name, message)
    print("Done.")
