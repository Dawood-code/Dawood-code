"""Turn Dawood's public GitHub avatar into a self-typing ASCII SVG."""

from __future__ import annotations

import argparse
import io
import os
from html import escape
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "dawood-ascii.svg"
DEFAULT_SOURCE = "https://avatars.githubusercontent.com/u/186283643?v=4&size=512"
RAMP = "@%#*+=-:. "


def load_image(source: str) -> Image.Image:
    if source.startswith(("http://", "https://")):
        response = requests.get(source, headers={"User-Agent": "Dawood-code-profile-readme/1.0"}, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    return Image.open(source).convert("RGB")


def isolate_subject(image: Image.Image) -> Image.Image:
    """Use a soft central portrait mask so the light rooftop does not become ASCII noise."""
    width, height = image.size
    image = image.crop((int(width * 0.18), int(height * 0.06), int(width * 0.82), height))
    width, height = image.size

    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((int(width * 0.25), 0, int(width * 0.76), int(height * 0.47)), fill=255)
    draw.polygon(
        [
            (int(width * 0.18), int(height * 0.38)),
            (int(width * 0.40), int(height * 0.31)),
            (int(width * 0.66), int(height * 0.31)),
            (int(width * 0.84), int(height * 0.40)),
            (width, height),
            (0, height),
        ],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, width // 80)))
    return Image.composite(image, Image.new("RGB", image.size, "white"), mask)


def ascii_rows(image: Image.Image, columns: int = 50) -> list[str]:
    image = isolate_subject(image)
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    rows = max(1, round(columns * gray.height / gray.width * 0.47))
    tiny = gray.resize((columns, rows), Image.Resampling.LANCZOS)

    output: list[str] = []
    for y in range(rows):
        chars: list[str] = []
        for x in range(columns):
            value = tiny.getpixel((x, y))
            index = min(len(RAMP) - 1, round(value / 255 * (len(RAMP) - 1)))
            chars.append(RAMP[index])
        output.append("".join(chars).rstrip())
    return output


def render(rows: list[str], static: bool = False) -> str:
    width = 370
    top = 53
    font_size = 7.2
    line_height = 8.2
    height = round(top + len(rows) * line_height + 13)
    text_width = 50 * font_size * 0.61

    defs: list[str] = []
    content: list[str] = []
    for index, row in enumerate(rows):
        y = top + index * line_height
        clip_id = f"row-{index}"
        delay = index * 0.034
        if static:
            defs.append(f'<clipPath id="{clip_id}"><rect x="18" y="{y - 7}" width="{text_width}" height="10" /></clipPath>')
        else:
            defs.append(
                f'<clipPath id="{clip_id}"><rect x="18" y="{y - 7}" width="0" height="10">'
                f'<animate attributeName="width" from="0" to="{text_width}" begin="{delay:.3f}s" dur=".62s" fill="freeze" />'
                "</rect></clipPath>"
            )
        content.append(
            f'<text x="18" y="{y:.1f}" clip-path="url(#{clip_id})" xml:space="preserve">{escape(row)}</text>'
        )

    cursor = ""
    if not static:
        finish = max(0.8, len(rows) * 0.034 + 0.62)
        cursor = f'''<rect x="18" y="{height - 20}" width="7" height="10" fill="#56d364">
    <animate attributeName="opacity" values="0;0;1;0;1" keyTimes="0;.78;.79;.89;1" dur="{finish + 1.4:.2f}s" fill="freeze" />
  </rect>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">ASCII portrait of Muhammad Dawood</title>
  <desc id="desc">A monochrome portrait types itself into a terminal window.</desc>
  <defs>{''.join(defs)}</defs>
  <style>
    text {{ fill:#c9d1d9; font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace; font-size:{font_size}px; }}
  </style>
  <rect x="0.5" y="0.5" width="369" height="{height - 1}" rx="14" fill="#0d1117" stroke="#30363d" />
  <circle cx="22" cy="22" r="5" fill="#ff5f57" />
  <circle cx="39" cy="22" r="5" fill="#febc2e" />
  <circle cx="56" cy="22" r="5" fill="#28c840" />
  <text x="78" y="27" fill="#8b949e" font-size="12">./portrait.sh</text>
  {''.join(content)}
  {cursor}
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Local image path or public image URL")
    args = parser.parse_args()
    rows = ascii_rows(load_image(args.source))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(rows, static=os.getenv("STATIC") == "1"), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
