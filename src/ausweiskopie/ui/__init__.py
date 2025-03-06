"""
UI of the Ausweiskopie app.
"""
import datetime
import tkinter as tk
import traceback
from collections import OrderedDict
from pydoc import classname
from tkinter import filedialog
from tkinter import messagebox
from typing import Mapping

from .dialogs import savefileasname
from .threads import foreground, background
from ..redact import Field, FIELDS_PASSPORT, FIELDS_NO_BACK
from ..redact import \
    FIELDS_VORLAEUFIG_BACK, FIELDS_VORLAEUFIG_FRONT, \
    FIELDS_NPA_FRONT_2021, FIELDS_NPA_FRONT_2010, FIELDS_NPA_FRONT_2019, \
    FIELDS_NPA_BACK

try:
    import ttkbootstrap as ttk
    STYLE = True
except ImportError:
    from tkinter import ttk
    STYLE = False

from .elements import DocumentFrame, Selection, ColorButton, \
    MarkFrame
from ..resources import \
    ICON, EXAMPLE_NPA_2021, EXAMPLE_NPA_BACK, get_resource, _, ICON_COLORED

from PIL import Image, ImageTk

ICON_IMAGE = Image.open(get_resource(ICON))
ICON_IMAGE_COLORED = Image.open(get_resource(ICON_COLORED))


class MainFrame(ttk.Frame):
    """Main application element."""
    def __init__(self, root):
        super(MainFrame, self).__init__(root)

        padding = {"padx": 8, "pady": 8}

        self.front = DocumentFrame(
            self, title=_("FRONT"),
            document_types={
                _("NPA_2021"):
                    FIELDS_NPA_FRONT_2021,
                _("NPA_2019"):
                    FIELDS_NPA_FRONT_2019,
                _("NPA_2010"):
                    FIELDS_NPA_FRONT_2010,
                _("VORLAEUFIG"):
                    FIELDS_VORLAEUFIG_FRONT,
                _("GERMAN_PASSPORT"):
                    FIELDS_PASSPORT,
            },
            default=get_resource(EXAMPLE_NPA_2021),
        )
        self.back = DocumentFrame(
            self, title=_("BACK"),
            document_types={
                _("NPA_BACK"):
                    FIELDS_NPA_BACK,
                _("VORLAEUFIG_BACK"):
                    FIELDS_VORLAEUFIG_BACK,
                _("NO_BACK"):
                    FIELDS_NO_BACK,
            },
            default=get_resource(EXAMPLE_NPA_BACK)
        )
        self.front.grid(row=0, column=0, sticky="E", **padding)
        self.back.grid(row=0, column=1, sticky="W", **padding)

        fields_set = ttk.Labelframe(self, text=_("REDACT_FIELDS"))
        note = ttk.Label(fields_set, text=_("NOT_ALL_PRESENT"))
        note.grid(row=0, column=0, sticky="W", **padding)

        fields = OrderedDict()
        for field in Field:
            fields[_(field)] = field

        self.select_fields = Selection(fields_set, fields, {
            Field.DOCUMENT_NUMBER, Field.CAN,
            Field.NAME_AT_BIRTH, Field.AUTHORITY,
            Field.HEIGHT, Field.COLOUR_OF_EYES,
        }, columns=4)
        self.select_fields.grid(row=1, column=0, sticky="WE", **padding)

        fields_set.grid_columnconfigure(0, weight=1)
        fields_set.grid_columnconfigure(1, weight=1)
        fields_set.grid(row=1, column=0, columnspan=2, sticky="WE", **padding)

        self.watermark = MarkFrame(self, text=_("MARK_COPY"))
        self.watermark.grid(row=2, column=0, columnspan=2, sticky="WE",
                            **padding)

        small = ICON_IMAGE.copy()
        small.thumbnail((24, 24))
        self._small = ImageTk.PhotoImage(small)

        button_bar = ttk.Frame(self)
        ttk.Label(button_bar, image=self._small) \
            .grid(row=0, column=0, sticky="W")
        ttk.Label(button_bar)\
            .grid(row=0, column=1, sticky="WE")
        ttk.Button(button_bar, text=_("PREVIEW"), command=self.preview)\
            .grid(row=0, column=2, sticky="E")
        create_button = ttk.Button(
            button_bar, text=_("CREATE_COPY"), command=self.save
        )
        create_button.grid(row=0, column=3, sticky="E")
        if STYLE:
            create_button.configure(bootstyle="success")
        button_bar.grid(row=3, column=0, columnspan=2, sticky="WES")
        button_bar.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        for i in range(2):
            self.grid_columnconfigure(i, weight=1)

    @property
    def _arguments(self) -> Mapping[str, object]:
        return {
            "text":
                self.watermark.text if self.watermark.use_watermark else "",
            "text_color": self.watermark.color,
            "redact_color": "black",
            "grayscale": self.watermark.grayscale,
            "redact_fields": self.select_fields.get_selections(),
            "text_transparency": self.watermark.percentage / 100
        }

    def preview(self, _=None):
        for doc in (self.back, self.front):
            doc.apply(**self._arguments, preview=True)

    def save(self, _=None):
        outfile = savefileasname(
            #confirmoverwrite=True,
            defaultextension=".pdf",
            filetypes=[
                ("Portable Document Format", "*.pdf"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Portable Network Graphic", "*.png"),
            ],
            parent=self.winfo_toplevel()
        )
        if not outfile:
            return

        # Create the pictures
        pages = []
        for doc in (self.front, self.back):
            if doc.skip:
                continue
            page = doc.apply(**self._arguments, preview=False)

            # Strip image metadata (software used, etc.)
            # No need to link identity documents to software versions.
            new = Image.new(page.mode, page.size)
            new.putdata(page.getdata())
            pages.append(page)

        if outfile.endswith(".pdf"):
            pages[0].save(
                outfile,
                save_all=True,
                append_images=pages[1:],
                title="",
                creationDate=1,
                modDate=1,
            )

    def finish(self):
        ...


def main():
    try:
        from gi.repository import GLib
        from threading import Thread

        loop = GLib.MainLoop()
        Thread(target=loop.run, name="GLib MainLoop").start()
    except ImportError:
        loop = None

    if hasattr(ttk, "Window"):
        root = ttk.Window()
    else:
        root = tk.Tk(className = "Ausweiskopie")

    foreground.instance = root

    try:
        root.wm_title("Meine Ausweiskopie")
        root.wm_iconphoto(False, ImageTk.PhotoImage(ICON_IMAGE_COLORED))

        m = MainFrame(root)
        m.pack(expand=1, fill="both")

        root.mainloop()
    finally:
        if loop is not None:
            loop.quit()
