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
    [cx-bg_r, cy-bg_r, cx+bg_r, cy+bg_r],
    radius=24, fill=(25, 15, 45, 245)
)

# Draw 6-pointed spark/star
for i in range(3):
    angle = math.radians(i * 60 - 90)
    angle_perp = angle + math.radians(90)
    inner_width = 30
    tip_width = 4

    p1x = cx + inner_width * math.cos(angle_perp)
    p1y = cy + inner_width * math.sin(angle_perp)
    p2x = cx + r * math.cos(angle) + tip_width * math.cos(angle_perp)
    p2y = cy + r * math.sin(angle) + tip_width * math.sin(angle_perp)
    p3x = cx + r * math.cos(angle) - tip_width * math.cos(angle_perp)
    p3y = cy + r * math.sin(angle) - tip_width * math.sin(angle_perp)
    p4x = cx - inner_width * math.cos(angle_perp)
    p4y = cy - inner_width * math.sin(angle_perp)

    draw.polygon([(p1x, p1y), (p2x, p2y), (p3x, p3y), (p4x, p4y)], fill=col)

# Small glow dots at each tip
for i in range(6):
    angle = math.radians(i * 60 - 90)
    tip_x = cx + (r + 6) * math.cos(angle)
    tip_y = cy + (r + 6) * math.sin(angle)
    draw.ellipse([tip_x-3, tip_y-3, tip_x+3, tip_y+3], fill=(220, 180, 255, 200))

# White "C" letter - simple approach
# Actually, let's keep it as just the spark logo, it's cleaner

ico_path = 'C:/Users/HP/Desktop/1/tools/claude-icon.ico'

img_256 = img
img_64 = img.resize((64, 64), Image.LANCZOS)
img_48 = img.resize((48, 48), Image.LANCZOS)
img_32 = img.resize((32, 32), Image.LANCZOS)
img_16 = img.resize((16, 16), Image.LANCZOS)

img_256.save(ico_path, 'ICO', sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
print(f"ICO created: {ico_path}")
print(f"Size: {os.path.getsize(ico_path)} bytes")
