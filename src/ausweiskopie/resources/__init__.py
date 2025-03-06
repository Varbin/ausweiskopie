"""
Resources for the package.
"""
import csv
import locale
import platform
import sys
from typing import Optional

from importlib_resources import files


__all__ = ["EXAMPLE_NPA_2010", "EXAMPLE_NPA_2019", "EXAMPLE_NPA_2021", "EXAMPLE_NPA_BACK", "FONT_NOTOSANS_REGULAR", "TRANSLATIONS", "ICON", "get_resource", "set_locale", "get_string", "_"]


EXAMPLE_NPA_2010 = "npa_2010.jpg"
EXAMPLE_NPA_2019 = "npa_2019.jpg"
EXAMPLE_NPA_2021 = "npa_2021.png"
EXAMPLE_NPA_BACK = "npa_back.png"

FONT_NOTOSANS_REGULAR = "NotoSans-Regular.ttf"

TRANSLATIONS = "translations.csv"

ICON = "icon.png"
ICON_COLORED = "icon_colored.png"

_locale: Optional[str] = None
_strings: dict[str, dict[str, str]] = {}


def get_resource(fn, mode="rb"):
    """Get a resource file."""
    return files(__name__).joinpath(fn).open(mode)


def set_locale(new_locale: Optional[str] = None):
    """Set the locale for every string lookup."""
    global _locale
    if new_locale is None:
        locale.setlocale(locale.LC_ALL, '')
        new_locale = locale.getlocale(
            locale.LC_CTYPE if platform.system() == "Windows"
                            else locale.LC_MESSAGES
        )[0]
        if new_locale == "C":
            new_locale = "en"
        else:
            new_locale = new_locale[:2].lower()
    _locale = new_locale


def get_string(key: str) -> str:
    """Return a translated string."""
    global _strings
    if not _strings:
        with get_resource(TRANSLATIONS, "r") as translations:
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

    # key = str(key)

    ret = _strings.get(key, {"en": key}).get(
        _locale, _strings.get("en", key)
    )
    if ret == key:
        print(f"Not translated: {key}", file=sys.stderr)

    return ret.replace("<br>", "\n")


_ = get_string
