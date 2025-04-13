import dataclasses
import datetime
import enum
import uuid
from typing import Optional, Tuple, Dict, List
from annotated_types import Gt

from pydantic import BaseModel
from typing_extensions import NotRequired, Annotated, TypedDict


class Side(str, enum.Enum):
    """Sides of id documents."""
    FRONT = "front"
    BACK = "back"


class Rectangle(TypedDict):
    """Rectangle on a side."""
    tl: Tuple[Annotated[float, Gt(0)], Annotated[float, Gt(0)]]
    br: Tuple[Annotated[float, Gt(0)], Annotated[float, Gt(0)]]


Layout = TypedDict("Layout", {
    Side.FRONT: Dict[str, List[Rectangle]],
    Side.BACK: NotRequired[Dict[str, List[Rectangle]]],
})


class MRZ(str, enum.Enum):
    """Possible ICAO MRZ variants.

    Other forms of MRZ (QR codes, PDF417, bar code) will get their own field.
    """
    TD1 = "TD-1"
    TD2 = "TD-2"
    TD3 = "TD-3"

    def coordinates(self) -> Dict[Side, Rectangle]:
        """Return the positions of the MRZ."""
        if self == MRZ.TD1:
            return {}
        elif self == MRZ.TD2:
            return {}
        elif self == MRZ.TD3:
            return {}


class Type(str, enum.Enum):
    """Possible document types"""
    # ID cards or papers
    ID = "id"

    # Passport (usually the copy of the bio card)
    PASSPORT = "passport"

    # Driving permits or similar licenses, they might serve as an id document
    DRIVING_PERMIT = "driving-permit"

    # Special passport-like travel documents for members of some organizations
    # (e.g., UN, Red-Cross, EU)
    LAISSEZ_PASSER = "laissez-passer"

    # Documents allowing to live in some country
    RESIDENCY_PERMIT = "residency-permit"

    # Some countries issue special seafarer documents (similar to passports) to
    # ease traveling from / to ships
    SEAFARER = "seafarer"

    # Other documents
    OTHER = "other"


class Subtype(str, enum.Enum):
    """Possible document subtypes"""
    # Temporary or emergency documents, issued if the original documents were
    # lost, or they need to be issued in a short amount of time
    TEMPORARY = "temporary"

    # Diplomatic passports issued for diplomats
    DIPLOMATIC = "diplomatic"

    # Service passports, issued for members of the state
    SERVICE = "service"

    # Other non-standard type of the document
    OTHER = "other"


@dataclasses.dataclass
class Metadata:
    """Document metadata"""
    issuer: str
    type: Type
    subtype: str
    issuedSince: datetime.date
    issuedUntil: Optional[datetime.date] = None
    revision: Optional[str] = None
    mrz: Optional[MRZ] = None
    mrzId: Optional[str] = None
    dimensions: Optional[str] = None
    dimensionsCustom: Optional[Tuple[float, float]] = None

    @property
    def dimensionSize(self) -> Tuple[float, float]:
        pass

@dataclasses.dataclass
class Document(BaseModel):
    id: uuid.UUID
    meta: Metadata
    layout: Layout
    i18n: Dict[str, Dict[str, str]]

    def merged_side(self, side: Side) -> List[Rectangle]:
        pass


