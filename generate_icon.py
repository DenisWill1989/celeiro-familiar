from PIL import Image, ImageDraw, ImageFont
import os

size = (512, 512)
img = Image.new("RGBA", size, "#02060D")
draw = ImageDraw.Draw(img)

# Outer glow / rings (Sci-Fi HUD style)
center = (256, 256)

# Multiple concentric tech rings
for r in [230, 220, 200, 175]:
    draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], outline=(0, 255, 204, 80), width=3)

# Dashed-like HUD marks
for angle_offset in range(0, 360, 30):
    import math
    rad = math.radians(angle_offset)
    x1 = center[0] + int(210 * math.cos(rad))
    y1 = center[1] + int(210 * math.sin(rad))
    x2 = center[0] + int(230 * math.cos(rad))
    y2 = center[1] + int(230 * math.sin(rad))
    draw.line([x1, y1, x2, y2], fill=(0, 242, 254, 200), width=4)

# Glowing inner circle
r_in = 160
draw.ellipse([center[0]-r_in, center[1]-r_in, center[0]+r_in, center[1]+r_in], fill=(7, 16, 30, 255), outline=(0, 255, 204, 255), width=6)

# Draw glowing Sci-Fi Dollar Sign "$"
# We will draw a stylized vector dollar symbol manually or with font
# Font search or custom geometric path for cyber "$"
# Central S-curves and vertical bar
# Vertical lines
draw.line([center[0], center[1]-110, center[0], center[1]+110], fill=(0, 255, 204, 255), width=14)
draw.line([center[0]-6, center[1]-110, center[0]-6, center[1]+110], fill=(0, 242, 254, 180), width=6)

# Draw cyber $ shape manually with crisp geometric segments
# Top bar
draw.line([center[0]+50, center[1]-80, center[0]-40, center[1]-80], fill=(0, 255, 204, 255), width=16)
# Top left vertical
draw.line([center[0]-40, center[1]-80, center[0]-40, center[1]-10], fill=(0, 255, 204, 255), width=16)
# Middle bar
draw.line([center[0]-40, center[1]-10, center[0]+40, center[1]+10], fill=(0, 255, 204, 255), width=16)
# Bottom right vertical
draw.line([center[0]+40, center[1]+10, center[0]+40, center[1]+80], fill=(0, 255, 204, 255), width=16)
# Bottom bar
draw.line([center[0]+40, center[1]+80, center[0]-50, center[1]+80], fill=(0, 255, 204, 255), width=16)

# Add glow / highlight dots
draw.ellipse([center[0]-40-10, center[1]-80-10, center[0]-40+10, center[1]-80+10], fill=(0, 255, 204, 255))
draw.ellipse([center[0]+40-10, center[1]+80-10, center[0]+40+10, center[1]+80+10], fill=(0, 255, 204, 255))

os.makedirs("static", exist_ok=True)
img.save("static/icon-512.png")
img.save("static/apple-touch-icon.png")
print("Icons generated successfully!")
