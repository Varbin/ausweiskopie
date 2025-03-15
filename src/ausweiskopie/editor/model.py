from dataclasses import dataclass
from typing import Optional

from ausweiskopie.redact import Location, Field
from ausweiskopie.resources import _


@dataclass
class FieldLocation:
    """ A document that records the location and type of field """

    location: Location
    field: Field

    rect_id: Optional[int]

    def __str__(self):
        return f"{_(self.field)} = {self.location}"
