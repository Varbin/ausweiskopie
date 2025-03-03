"""
Redact fields of identity documents.
"""

from typing import Collection

from .definitions import *
from .fields import *
from PIL import Image
from PIL import ImageDraw


__all__ = [
    "redact",
    "Field",
    "FieldDefinition",
    "Location",
    "FIELDS_NPA_BACK",
    "FIELDS_NPA_FRONT_2021",
    "FIELDS_NPA_FRONT_2019",
    "FIELDS_NPA_FRONT_2010",
    "FIELDS_VORLAEUFIG_BACK",
    "FIELDS_VORLAEUFIG_FRONT",
    "FIELDS_PASSPORT"
]


def redact(image: Image,
           fields_to_redact: Collection[Field],
           field_definitions: FieldDefinition,
           show_instead_of_redact=False,
           color="black",
           ) -> Image:
    """
    Redact redacts a document.

    :param image:
    :param fields_to_redact:
    :param field_definitions:
    :param show_instead_of_redact:
    :param color:
    :return:
    """

    draw = ImageDraw.Draw(image)
    fill = None if show_instead_of_redact else color

    for field in fields_to_redact:
        for definition in field_definitions.get(field, ()):
            coordinates = definition.rectangle_coordinates(image)
            draw.rectangle(coordinates, fill, color)

    return image
