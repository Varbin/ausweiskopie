"""
Resources for the package.
"""
import csv
import json
import locale
import sys
import uuid
from pathlib import Path
from typing import NewType, Optional, Union, Literal, Iterable, Callable, \
    BinaryIO, cast

import tomli
from importlib_resources import files

from .document import Side, Rectangle, Layout, MRZ, Type, Subtype, Dimension, \
    Metadata, Document

__all__ = ["EXAMPLE_NPA_2010", "EXAMPLE_NPA_2019", "EXAMPLE_NPA_2021", "EXAMPLE_NPA_BACK", "EXAMPLE_CH_NIDK_2023", "EXAMPLE_CH_NIDK_2023_BACK", "FONT_NOTOSANS_REGULAR", "TRANSLATIONS", "ICON", "get_resource", "set_locale", "get_string", "_",
           "Side", "Rectangle", "Layout", "MRZ", "Type", "Subtype", "Dimension", "Metadata", "Document",
           "load_documents", "document_title"
]


EXAMPLE_NPA_2010 = "npa_2010.jpg"
EXAMPLE_NPA_2019 = "npa_2019.jpg"
EXAMPLE_NPA_2021 = "npa_2021.png"
EXAMPLE_NPA_BACK = "npa_back.png"
EXAMPLE_CH_NIDK_2023 = "ch_nidk_front.jpg"
EXAMPLE_CH_NIDK_2023_BACK = "ch_nidk_back.jpg"

FONT_NOTOSANS_REGULAR = "NotoSans-Regular.ttf"

TRANSLATIONS = "translations.csv"

ICON = "icon.png"
ICON_COLORED = "icon_colored.png"

_locale: Optional[str] = None
_strings: dict[str, dict[str, str]] = {}

# Ensure only "valid" directories can be passed to list_resources.
ResourceDirectory = NewType("ResourceDirectory", str)
DOCUMENTS = ResourceDirectory("documents")
SCHEMAS = ResourceDirectory("schemas")


def list_resources(directory: ResourceDirectory) -> list[Path]:
    """Returns an array of filenames in a resources directory.
    Each file name can be passed to get_resource()."""
    base = files(__name__)
    return list(map(lambda p: p.relative_to(base), base.joinpath(directory).iterdir()))


def get_resource(fn, mode: Literal["r", "rb"] = "rb", *args, **kwargs):
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


def get_locale() -> str:
    """Returns the locale."""
    if _locale is None:
        set_locale()
    return _locale



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


def load_document(fd: BinaryIO, toml: bool = False) -> Document:
    """Parses a document from a binary file descriptor."""
    if toml:
        obj = tomli.load(fd)
    else:
        obj = json.load(fd)

    return Document.model_validate(obj)


def load_documents(
        internal_documents: bool = False,
        additional_paths: Iterable[Union[str, Path]] = (),
        progress: Optional[Callable[[int, int], None]] = None,
        conflict: Optional[Callable[[Document, Document], int]] = None,
        error: Optional[Callable[[str, Exception], bool]] = None,
) -> dict[uuid.UUID, Document]:
    """Load document definitions (JSON or TOML)
    from the given paths and by default all internal ones.
    Paths will not be searched recursively.

    You can pass callbacks for interactive usage.
    The progress function takes the already parsed and maximum values.
    The conflict function takes two documents,
    and returns the index for the chosen one.
    The function may return 2 to keep both.
    If loading a document throws an exception,
    the error function together with the filename will be called.
    The function should return true to supress the error.
    """
    documents = {}
    loaded = 0

    def report_progress():
        """Call the progress function if defined."""
        if progress is not None:
            progress(loaded, len(internal_docs) + len(external_docs))

    internal_docs = []
    external_docs = []
    if internal_documents:
        internal_docs = list_resources(DOCUMENTS)

    for path in additional_paths:
        external_docs.extend(Path(path).glob("*.json"))
        external_docs.extend(Path(path).glob("*.toml"))

    report_progress()

    for doc in internal_docs:
        loaded += 1
        with get_resource(doc, 'rb') as res:
            res = cast(BinaryIO, res)
            document = load_document(res, doc.suffix == '.toml')

            # No collision detection on internal document definitions
            documents[document.id] = document

            report_progress()

    for doc in external_docs:
        loaded += 1
        try:
            with open(doc, 'rb') as res:
                # open with 'rb' always returns a BytesIO,
                # but PyCharm does not know this.
                res = cast(BinaryIO, res)
                document = load_document(res, doc.suffix == '.toml')
        except (ValueError, IOError) as e:
            if error is not None:
                if error(str(doc), e):
                    continue
                else:
                    raise e
            else:
                raise e

        if document.id in documents.keys() and conflict is not None:
            ret = conflict(documents[document.id], document)
            if ret == 0:
                continue
            elif ret == 1:
                pass
            else:
                document.id = uuid.uuid4()

        documents[document.id] = document
        report_progress()

    report_progress()
    return documents


def document_title(document: Document) -> str:
    title = document.i18n["DOCUMENT_NAME"]
    return title.get(get_locale(), title['en'])
