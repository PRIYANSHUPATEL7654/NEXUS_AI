from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIRECTORY = Path(__file__).resolve().parent.parent / "public" / "icons"


def font_for(size: int):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_icon(size: int) -> None:
    image = Image.new("RGB", (size, size), "#0b1220")
    draw = ImageDraw.Draw(image)
    margin = round(size * 0.14)
    radius = round(size * 0.19)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill="#2754d7",
        outline="#7897ee",
        width=max(2, round(size * 0.012)),
    )
    font = font_for(round(size * 0.48))
    text_box = draw.textbbox((0, 0), "N", font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    draw.text(
        ((size - text_width) / 2, (size - text_height) / 2 - text_box[1]),
        "N",
        font=font,
        fill="white",
    )
    image.save(OUTPUT_DIRECTORY / f"icon-{size}.png", optimize=True)


if __name__ == "__main__":
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for icon_size in (192, 512):
        create_icon(icon_size)
