import dataclasses
import datetime
import enum
import uuid
from typing import Optional, Tuple, Dict, List

from annotated_types import Gt
from pydantic import BaseModel
from typing_extensions import NotRequired, Annotated, TypedDict

from ..redact import Location


class Side(str, enum.Enum):
    """Sides of id documents."""
    FRONT = "front"
    BACK = "back"


class Rectangle(TypedDict):
    """Rectangle on a side."""
    tl: Tuple[Annotated[float, Gt(0)], Annotated[float, Gt(0)]]
    br: Tuple[Annotated[float, Gt(0)], Annotated[float, Gt(0)]]

    def location(self) -> Location:
        return Location(self.tl, self.br)

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
        # TODO: Implement
        if self == MRZ.TD1:
            return {}
        elif self == MRZ.TD2:
            return {}
        elif self == MRZ.TD3:
            return {}
        else:
            raise NotImplementedError(f"MRZ coordinates not implemented for {self}")


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

    # Travel documents issued to stateless persons
    STATELESS = "stateless"

    # Travel documents issued to non-citizens
    NONCITIZEN = "noncitizen"

    # Travel documents issued to refugess
    REFUGEE = "refugee"

    # Other non-standard type of the document
    OTHER = "other"


class Dimension(str, enum.Enum):
    """Possible document dimensions (i.e. proportions)"""
    # Standard "credit card" size; also known as CR-80 or TD1
    ID1 = "ID-1"
    # Paper visas, temporary IDs, also the old style Ausweis
    ID2 = "ID-2"
    # Passport booklets
    ID3 = "ID-3"
    # Some rarer kind
    CR90 = "CR-90"
    # Size is defined in a different property.
    CUSTOM = "custom"

    def size(self) -> Tuple[float, float]:
        """Returns values of a dimension in millimeters."""
        if self == Dimension.ID1:
            return 85.6, 53.98
        if self == Dimension.ID2:
            return 105, 74
        if self == Dimension.ID3:
            return 125, 88
        if self == Dimension.CR90:
            return 92, 60

        raise NotImplementedError("A custom dimension has no size.")


@dataclasses.dataclass
class Metadata:
    """Document metadata"""
    dimensions: Dimension  # How large is this document
    issuer: str  # Issuing country
    type: Type  # What type of document is this
    issuedSince: datetime.date  # Since when is this kind of document in circulation?

    subtype: Optional[Subtype] = None
    issuedUntil: Optional[datetime.date] = None  # None = currently issued
    revision: Optional[str] = None
    mrz: Optional[MRZ] = None
    mrzId: Optional[str] = None
    dimensionsCustom: Optional[Tuple[float, float]] = None

    @property
    def dimensionSize(self) -> Tuple[float, float]:
        """Returns the dimensions of a document in millimetres,
        independent of if a well known dimension is passed or a custom one."""
        if self.dimensions != Dimension.CUSTOM:
            return self.dimensions.size()
        return self.dimensionsCustom


@dataclasses.dataclass
class Document(BaseModel):
    """Document describes a single revision of a type of identity document.
    Every revision must have a different id."""
    id: uuid.UUID
    meta: Metadata
    layout: Layout
    i18n: Dict[str, Dict[str, str]]

