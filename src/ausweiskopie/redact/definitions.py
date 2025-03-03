"""
Front and back of an identity documents.
"""
from collections import namedtuple
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Mapping, Collection

from PIL import Image

from typing import Any, Union

Coordinates = namedtuple("Coordinates", "x y")


@dataclass
class Location:
    """
    Coordinates are relative coordinates (0-1.0) from the top left corner of
    an image.
    """
    top_left: Union[Coordinates, tuple[float, float]]
    bottom_right: Union[Coordinates, tuple[float, float]]

    def rectangle_coordinates(self, image: Image) \
            -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Converts the relative top_left and bottom_right coordinates to
        ones usable by Pillow.
        """

        top_left = Coordinates(*self.top_left)
        bottom_right = Coordinates(*self.bottom_right)

        return (
            (int(image.width*top_left.x),
             int(image.height*top_left.y)),
            (int(image.width*bottom_right.x),
             int(image.height*bottom_right.y)),
        )


class _AutoName(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int,
                              last_values: list[Any]) -> Any:
        return name


class Field(str, _AutoName):
    """Individual fields found on a German identity document."""
    DOCUMENT_NUMBER = auto()
    MACHINE_READABLE_ZONE = auto()

    PHOTO = auto()

    SURNAME = auto()
    GIVEN_NAME = auto()
    NAME_AT_BIRTH = auto()
    RELIGIOUS_NAME_OR_PSEUDONYM = auto()
    ADDRESS = auto()
    SIGNATURE = auto()

    DATE_OF_BIRTH = auto()
    PLACE_OF_BIRTH = auto()

    COLOUR_OF_EYES = auto()
    HEIGHT = auto()

    NATIONALITY = auto()
    SEX = auto()

    DATE_OF_EXPIRY = auto()
    DATE = auto()
    AUTHORITY = auto()

    # Required for unlocking after second wrong PIN entry.
    CAN = auto()

    # Found on Aufenthaltstiteln
    REMARKS = auto()

    def __str__(self):
        return self.value


FieldDefinition = Mapping[Field, Sequence[Location]]
