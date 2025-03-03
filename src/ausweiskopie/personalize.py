"""
"Personalize" a copy - convert it to grayscale, add "COPY", and a recipient.
"""

import math

from random import SystemRandom
from string import Template
from typing import Literal

from .resources import get_resource, FONT_NOTOSANS_REGULAR

from PIL import Image, ImageColor, ImageChops, ImageDraw, ImageFont, ImageOps

TEXT_COPY = "KOPIE"
TEXT_COPY_DO_NOT_COPY = "KOPIE - WEITERGABE UNTERSAGT"
TEXT_FULL = (
    "KOPIE \n\n"
    "erstellt am $date\n"
    "für \"$recipient\"\n"
    "zum Zwecke\n"
    "$use\n\n"
    "KOPIE"
)


def is_grayscale(image: Image):
    """is_grayscale returns if an image is grayscale or black and white"""
    if image.mode == "L":
        return True

    image = image.convert("RGB")

    rgb = image.split()
    return (
            ImageChops.difference(rgb[0], rgb[1]).getextrema()[1] == 0 and
            ImageChops.difference(rgb[0], rgb[2]).getextrema()[1] == 0
    )


def text_dimensions(text, font: ImageFont.FreeTypeFont,
                    anchor="la",
                    align: Literal["center", "left", "right"] = "center",
                    spacing=1.8):
    image = Image.new("L", (10000, 10000), "black")
    draw = ImageDraw.Draw(image)

    (tx, ty, bx, by) = draw.multiline_textbbox(
        (image.width / 2, image.height / 2),
        text,
        font,
        anchor,
        spacing,
        align
    )

    return abs(tx - bx), abs(ty - by)


def random_color() -> tuple[int, ...]:
    """Return a random, dark, color."""
    return tuple(SystemRandom().randint(0, 192) for _ in range(3))


def pattern(w, h):
    """Generate a random pattern based on the sinus function."""
    picture = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(picture)

    i = 15

    for height in range(0, h, int(i / 1.5)):
        color = random_color()
        size = SystemRandom().randint(i // 2, i * 4)
        p = SystemRandom().random() / 2 + 0.5

        x = p * math.tau
        points = []

        for width in range(0, w, 5):
            x += p
            y = math.sin(x) * size

            points.append((int(width), int(height + y)))

        draw.line(points, width=2, fill=color)
    return picture


def personalize(image: Image,
                grayscale: bool = True,
                text: str = TEXT_FULL,
                text_color: str = "red",
                text_transparency: float = 0.5,
                data=None):
    """
    Personalize a copy by converting it to grayscale and add (individual) text.

    :param image:
    :param grayscale:
    :param text:
    :param text_color:
    :param text_transparency:
    :param data:
    :return:
    """

    text = Template(text).safe_substitute(data or {})

    font_path = FONT_NOTOSANS_REGULAR
    anchor = "mm"
    align: Literal["center"] = "center"
    spacing = 1.5
    base = 10

    if text:
        font10 = ImageFont.truetype(get_resource(font_path), base)
        text_width, text_height = text_dimensions(text, font10, "la",
                                                  align, spacing)

        print(f"Base height: {text_height}, base width: {text_width}")
        print(f"Image height: {image.height}, image width: {image.width}")
        font_scale = min((
            image.width / text_width,
            image.height / text_height
        ))
        print(font_scale)
        font = ImageFont.truetype(get_resource(font_path),
                                  int(base*font_scale))

        color = ImageColor.getrgb(text_color)
        layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.ImageDraw(layer)
        draw.multiline_text(
            (image.width // 2, image.height // 2),
            # (0, 0),
            text,
            fill=color + (int(round(255*text_transparency, 0)),),
            font=font,
            anchor=anchor,
            spacing=spacing,
            align=align
        )
        image = Image.alpha_composite(image.convert("RGBA"), layer)\
            .convert("RGB")

    if grayscale and not is_grayscale(image):
        image = ImageOps.grayscale(image)

    return image
