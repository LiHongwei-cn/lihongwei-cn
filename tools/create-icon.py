"""Generate Claude AI star icon (ICO) for desktop shortcut."""
from PIL import Image, ImageDraw
import math, os

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

cx, cy = size // 2, size // 2
r = 90
col = (200, 150, 255, 255)

# Dark rounded-square background
bg_r = 112
draw.rounded_rectangle(
    [cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r],
    radius=24, fill=(25, 15, 45, 245)
)

# 6-pointed spark/star (Claude AI logo style)
for i in range(3):
    angle = math.radians(i * 60 - 90)
    angle_perp = angle + math.radians(90)
    inner_w, tip_w = 30, 4

    draw.polygon([
        (cx + inner_w * math.cos(angle_perp), cy + inner_w * math.sin(angle_perp)),
        (cx + r * math.cos(angle) + tip_w * math.cos(angle_perp), cy + r * math.sin(angle) + tip_w * math.sin(angle_perp)),
        (cx + r * math.cos(angle) - tip_w * math.cos(angle_perp), cy + r * math.sin(angle) - tip_w * math.sin(angle_perp)),
        (cx - inner_w * math.cos(angle_perp), cy - inner_w * math.sin(angle_perp)),
    ], fill=col)

# Glow dots at tips
for i in range(6):
    angle = math.radians(i * 60 - 90)
    tx = cx + (r + 6) * math.cos(angle)
    ty = cy + (r + 6) * math.sin(angle)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(220, 180, 255, 200))

ico_path = os.path.join(os.path.dirname(__file__), 'claude-icon.ico')
img_256 = img
img_64 = img.resize((64, 64), Image.LANCZOS)
img_48 = img.resize((48, 48), Image.LANCZOS)
img_32 = img.resize((32, 32), Image.LANCZOS)
img_16 = img.resize((16, 16), Image.LANCZOS)

img_256.save(ico_path, 'ICO', sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
print(f"OK: {ico_path} ({os.path.getsize(ico_path)} bytes)")
