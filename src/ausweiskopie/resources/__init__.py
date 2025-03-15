"""
Resources for the package.
"""
import csv
import locale
import platform
import sys
import typing
from typing import Optional

from importlib_resources import files


__all__ = ["EXAMPLE_NPA_2010", "EXAMPLE_NPA_2019", "EXAMPLE_NPA_2021", "EXAMPLE_NPA_BACK", "EXAMPLE_CH_ID_2023", "EXAMPLE_CH_ID_2023_BACK", "FONT_NOTOSANS_REGULAR", "TRANSLATIONS", "ICON", "get_resource", "set_locale", "get_string", "_"]


EXAMPLE_NPA_2010 = "npa_2010.jpg"
EXAMPLE_NPA_2019 = "npa_2019.jpg"
EXAMPLE_NPA_2021 = "npa_2021.png"
EXAMPLE_NPA_BACK = "npa_back.png"
EXAMPLE_CH_ID_2023 = "ch_nidk_front.jpg"
EXAMPLE_CH_ID_2023_BACK = "ch_nidk_back.jpg"

FONT_NOTOSANS_REGULAR = "NotoSans-Regular.ttf"

TRANSLATIONS = "translations.csv"

ICON = "icon.png"
ICON_COLORED = "icon_colored.png"

_locale: Optional[str] = None
_strings: dict[str, dict[str, str]] = {}


def get_resource(fn, mode="rb", *args, **kwargs):
    """Get a resource file."""
    return files(__name__).joinpath(fn).open(mode, *args, **kwargs)


def set_locale(new_locale: Optional[str] = None):
    """Set the locale for every string lookup."""
    global _locale
    if new_locale is None:
        locale.setlocale(locale.LC_ALL, '')
        new_locale = locale.getlocale(
	        getattr(locale, "LC_MESSAGES", locale.LC_CTYPE)
        )[0]
        if new_locale is None or new_locale == "C":
            new_locale = "en"
        else:
            new_locale = new_locale[:2].lower()
    _locale = new_locale


def get_string(key: str) -> str:
    """Return a translated string."""
    global _strings
    if not _strings:
        with get_resource(TRANSLATIONS, "r", encoding='utf-8') as translations:
            reader = csv.reader(translations, delimiter=";")
            heading = next(reader)
            keys = heading[1:]
            for row in reader:
                _strings[row[0]] = {
                    lang: translation for lang, translation in
                    zip(keys, row[1:])
                }

    if not _locale:
        set_locale()
    assert _locale is not None

    # key = str(key)

    ret = _strings.get(key, {"en": key}).get(
        _locale, _strings.get("en", key)
    )
    if ret == key:
        print(f"Not translated: {key}", file=sys.stderr)

    return ret.replace("<br>", "\n")  # type: ignore


_ = get_string
