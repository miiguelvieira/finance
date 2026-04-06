"""Gera assets/icon.ico programaticamente com Pillow."""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow não encontrado. Instale com: pip install Pillow>=10.0")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icon.ico"

BG = "#1e293b"
FG = "#ffffff"
SIZE = 256
SIZES = [16, 32, 48, 64, 128, 256]


def make_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    font_size = max(int(size * 0.65), 8)
    font = None
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(name, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "F", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), "F", fill=FG, font=font)
    return img


def main() -> None:
    frames = [make_frame(s) for s in SIZES]
    base = frames[-1]  # 256x256 como base
    base.save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[:-1],
    )
    print(f"Ícone gerado: {OUT}")


if __name__ == "__main__":
    main()
