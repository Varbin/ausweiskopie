from enum import Enum
from typing import Tuple, Mapping


class Names(str, Enum):
    ID1 = "ID-1"
    ID2 = "ID-2"
    ID3 = "ID-3"
    CR90 = "CR90"

VALUES: Mapping[Names, Tuple[int, int]] = {
    Names.ID1: (856, 540),
    Names.ID2: (1005, 740),
    Names.ID3: (1250, 880),
    Names.CR90: (920, 600),
}
