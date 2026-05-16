from PIL import Image, ImageDraw
from pathlib import Path

# Create input/images directory
images_dir = Path("input/images")
images_dir.mkdir(parents=True, exist_ok=True)

# Sample image 1: Red/white grid pattern (simulating aquarium tank)
img1 = Image.new("RGB", (900, 900), color=(20, 20, 30))
draw1 = ImageDraw.Draw(img1)

# Border
draw1.rectangle([50, 50, 850, 850], outline=(200, 50, 50), width=8)

# Internal grid
for i in range(100, 800, 100):
    draw1.line([(i, 50), (i, 850)], fill=(200, 50, 50), width=2)
    draw1.line([(50, i), (850, i)], fill=(200, 50, 50), width=2)

# Fill some cells with accent color
draw1.rectangle([100, 100, 250, 250], fill=(100, 30, 30))
draw1.rectangle([650, 650, 800, 800], fill=(100, 30, 30))

img1.save(images_dir / "sample1.jpg")
print(f"✓ Created sample1.jpg")

# Sample image 2: Diagonal stripes pattern
img2 = Image.new("RGB", (900, 900), color=(30, 30, 20))
draw2 = ImageDraw.Draw(img2)

# Border
draw2.rectangle([50, 50, 850, 850], outline=(200, 50, 50), width=8)

# Diagonal stripes (simulating aquarium with fish)
for i in range(0, 1000, 60):
    draw2.line([(i, 0), (i + 900, 900)], fill=(200, 50, 50), width=3)

# Add some circles to simulate fish
draw2.ellipse([150, 300, 250, 400], fill=(150, 100, 50))
draw2.ellipse([700, 500, 800, 600], fill=(150, 100, 50))

img2.save(images_dir / "sample2.jpg")
print(f"✓ Created sample2.jpg")

print(f"\nサンプル画像を生成しました:")
print(f"  - input/images/sample1.jpg")
print(f"  - input/images/sample2.jpg")
