"""Render terminal log as a PNG screenshot."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

LOG_FILE = Path("D:/xiaomi/codeguard-agent/docs/terminal-log.txt")
OUTPUT_FILE = Path("D:/xiaomi/codeguard-agent/docs/terminal-screenshot.png")

# Read log
lines = Path(LOG_FILE).read_text(encoding="utf-8").rstrip("\n").split("\n")

# Fonts - try to find a good monospace font on Windows
font_paths = [
    "C:/Windows/Fonts/consola.ttf",    # Consolas
    "C:/Windows/Fonts/courbd.ttf",     # Courier New Bold
    "C:/Windows/Fonts/cour.ttf",       # Courier New
    "C:/Windows/Fonts/msgothic.ttf",   # MS Gothic
]

font_size = 14
font = None
for fp in font_paths:
    try:
        font = ImageFont.truetype(fp, font_size)
        break
    except (OSError, IOError):
        continue

if font is None:
    font = ImageFont.load_default()

BOLD_FONT = None
for fp in font_paths[:2]:
    try:
        BOLD_FONT = ImageFont.truetype(fp, font_size)
        break
    except (OSError, IOError):
        pass

if BOLD_FONT is None:
    BOLD_FONT = font

# Measure text to determine image size
test_img = Image.new("RGB", (1, 1))
test_draw = ImageDraw.Draw(test_img)

max_line_width = 0
line_heights = []
for line in lines:
    if line:
        bbox = test_draw.textbbox((0, 0), line.strip("\r"), font=font)
        w = bbox[2] - bbox[0]
    else:
        w = 0
    max_line_width = max(max_line_width, w)
    line_heights.append(font_size + 3)

# Image dimensions
padding_x = 30
padding_y = 30
img_width = min(max_line_width + 2 * padding_x, 1920)
img_height = sum(line_heights) + 2 * padding_y

# Colors
BG = (22, 22, 22)        # Dark terminal background
FG = (200, 200, 200)      # Light gray text
FG_DIM = (120, 120, 120)  # Dim text
FG_GREEN = (100, 220, 100) # Success
FG_RED = (255, 80, 80)    # Error / critical
FG_YELLOW = (255, 200, 60) # Warning
FG_CYAN = (80, 200, 220)  # Info / cyan
FG_WHITE = (255, 255, 255) # Bold white

img = Image.new("RGB", (img_width, img_height), BG)
draw = ImageDraw.Draw(img)

y = padding_y
for i, line in enumerate(lines):
    text = line.strip("\r")
    if not text.strip():
        y += line_heights[i]
        continue

    # Color logic
    color = FG
    use_bold = False

    lowered = text.lower()
    if any(kw in lowered for kw in ["critical", "failed", "error", "--- original", "high blast"]):
        color = FG_RED
        use_bold = True
    elif any(kw in lowered for kw in ["high", "warning", "medium"]):
        color = FG_YELLOW
    elif any(kw in lowered for kw in ["pass", "ok", "complete", "success", "+++ suggested"]):
        color = FG_GREEN
    elif any(kw in lowered for kw in ["scanner", "analyzer", "refactor", "validator", "stage", "pipeline"]):
        color = FG_CYAN
        use_bold = True
    elif any(kw in lowered for kw in ["detail", "estimated", "deployment", "token", "total"]):
        color = FG_WHITE
    elif "[ FILE ]" in text or "file:" in lowered:
        color = FG_CYAN
    elif text.startswith("  [") or "[file]" in lowered:
        color = FG_CYAN
    elif "===" in text or "---" in text:
        color = FG_DIM
    elif text.startswith("  " + "=") or text.startswith("  " + "-"):
        color = FG_DIM

    draw_font = BOLD_FONT if use_bold else font
    x = padding_x

    # Truncate if too wide
    bbox = draw.textbbox((0, 0), text, font=draw_font)
    text_width = bbox[2] - bbox[0]
    if text_width > img_width - 2 * padding_x:
        # Try to fit
        while text and text_width > img_width - 2 * padding_x:
            text = text[:-1]
            bbox = draw.textbbox((0, 0), text + "...", font=draw_font)
            text_width = bbox[2] - bbox[0]
        text = text + "..."

    draw.text((x, y), text, font=draw_font, fill=color)
    y += line_heights[i]

img.save(OUTPUT_FILE, "PNG", optimize=True)
print(f"Saved: {OUTPUT_FILE}")
print(f"Size: {img_width}x{img_height}")
