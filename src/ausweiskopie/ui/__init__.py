"""
UI of the Ausweiskopie app.
"""
import datetime
import os
import sys
import tkinter as tk
import traceback
import uuid
from collections import OrderedDict
from pydoc import classname
from tkinter import filedialog
from tkinter import messagebox
from typing import Mapping

from .dialogs import savefileasname
from .threads import foreground, background
from ..editor.window import EditorFrame
from ..redact import Field, FIELDS_PASSPORT, FIELDS_NO_BACK, FIELDS_CH_NIDK_2023_FRONT, FIELDS_CH_NIDK_2023_BACK
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
    ICON, EXAMPLE_NPA_2021, EXAMPLE_NPA_BACK, get_resource, _, ICON_COLORED, \
    document_title, Document, Side, load_documents

from PIL import Image, ImageTk

ICON_IMAGE = Image.open(get_resource(ICON))
ICON_IMAGE_COLORED = Image.open(get_resource(ICON_COLORED))


def _get_version() -> str:
    try:
        import importlib.metadata
        return importlib.metadata.distribution('ausweiskopie').version
    except ImportError:
        import pkg_resources
        return pkg_resources.get_distribution('ausweiskopie').version


class MainFrame(ttk.Frame):
    """Main application element."""
    def __init__(self, root,  documents: dict[uuid.UUID, Document]):
        super(MainFrame, self).__init__(root)

        padding = {"padx": 8, "pady": 8}

        # TODO: Refactor
        # We need multiple data structures:
        # An ordered list for the ui elements,
        # and the dictionary that keeps them unique.
        self.documents = documents
        self.documents_sorted = sorted(documents.values(), key=document_title)

        row = 0

        self.front = DocumentFrame(
            self, title=_("FRONT"),
            default=get_resource(EXAMPLE_NPA_2021),
            side=Side.FRONT,
            document=self.documents_sorted[0],
        )
        self.back = DocumentFrame(
            self, title=_("BACK"),
            default=get_resource(EXAMPLE_NPA_BACK),
            side=Side.BACK,
            document=self.documents_sorted[0],
        )
        self.front.grid(row=row, column=0, sticky="E", **padding)
        self.back.grid(row=row, column=1, sticky="W", **padding)

        row += 1

        document_type = ttk.LabelFrame(self, text=_("DOCUMENT_TYPE"))
        self.document_selection = ttk.Combobox(
            document_type,
        )
        self.document_selection.configure(state="readonly")
        # TODO: Do proper sorting
        self.document_selection["values"] = tuple(
            map(document_title, self.documents_sorted)
        )
        self.document_selection.current(0)
        self.document_selection.bind("<<ComboboxSelected>>", self._on_doc_type_changed)
        self.document_selection.pack(expand=1, fill="x", **padding)
        document_type.grid(row=row, column=0, columnspan=2, sticky="WE", **padding)

        row += 1

        fields_set = ttk.Labelframe(self, text=_("REDACT_FIELDS"))
        note = ttk.Label(fields_set, text=_("NOT_ALL_PRESENT"))
        note.grid(row=0, column=0, sticky="W", **padding)

        fields = OrderedDict()
        for field in Field:
            fields[_(field)] = field

        self.select_fields = Selection(
            fields_set, self.documents_sorted[0], 4
        )
#                                       fields, {
#            Field.DOCUMENT_NUMBER, Field.CAN,
#            Field.NAME_AT_BIRTH, Field.AUTHORITY,
#            Field.HEIGHT, Field.COLOUR_OF_EYES,
 #       }, columns=4)
        self.select_fields.grid(row=row, column=0, sticky="WE", **padding)

        fields_set.grid_columnconfigure(0, weight=1)
        fields_set.grid_columnconfigure(1, weight=1)
        fields_set.grid(row=row, column=0, columnspan=2, sticky="WE", **padding)

        row += 1

        self.watermark = MarkFrame(self, text=_("MARK_COPY"))
        self.watermark.grid(row=row, column=0, columnspan=2, sticky="WE",
                            **padding)

        row += 1

        small = ICON_IMAGE.copy()
        small.thumbnail((24, 24))
        self._small = ImageTk.PhotoImage(small)

        button_bar = ttk.Frame(self)
        ttk.Label(button_bar, image=self._small) \
            .grid(row=0, column=0, sticky="W")
        ttk.Label(button_bar, text=" "+_get_version())\
            .grid(row=0, column=1, sticky="WE")
        ttk.Button(button_bar, text=_("PREVIEW"), command=self.preview)\
            .grid(row=0, column=2, sticky="E")
        create_button = ttk.Button(
            button_bar, text=_("CREATE_COPY"), command=self.save
        )
        create_button.grid(row=0, column=3, sticky="E")
        if STYLE:
            create_button.configure(bootstyle="success")
        button_bar.grid(row=row, column=0, columnspan=2, sticky="WES")
        button_bar.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        for i in range(2):
            self.grid_columnconfigure(i, weight=1)

        self._on_doc_type_changed(None)

    def _on_doc_type_changed(self, _):
        doc = self.documents_sorted[self.document_selection.current()]
        self.select_fields.document = doc
        self.front.document = doc
        self.back.document = doc

        #try:
        #    front = self.front
        #    back = self.back
        #except AttributeError:
        #    return

        #front.document = self.documents_ordered[self._document_type.get()]

        #print('Selected doc types: FRONT={}, BACK={}'.format(front.document_selection.get(), back.document_selection.get()))
        #all_fields_set = (set(front.document_types[front.document_selection.get()].keys())
        #                  | set(back.document_types[back.document_selection.get()].keys()))
        #self.select_fields.set_visible_fields([_(str(x)) for x in all_fields_set])


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
        result = savefileasname(
            #confirmoverwrite=True,
            defaultextension=".pdf",
            filetypes=[
                ("Portable Document Format", "*.pdf"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Portable Network Graphic", "*.png"),
            ],
            parent=self.winfo_toplevel()
        )
        if result is None:
            return

        outfile, ext = result
        if ext.lower() not in (".pdf", ".jpg", ".jpeg", ".png"):
            ext = ".pdf"

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

        try:
            if ext.lower() == ".pdf":
                pages[0].save(
                    outfile,
                    save_all=True,
                    append_images=pages[1:],
                    title="",
                    creationDate=1,
                    modDate=1,
                    format="pdf"
                )
            else:
                if ext.lower() == ".jpg":
                    ext = ".jpeg"
                height = sum(page.height for page in pages)
                width = max(page.width for page in pages)

                out = Image.new("RGB", (width, height), color="white")
                heightidx = 0
                for page in pages:
                    out.paste(page, (0, heightidx))
                    heightidx += page.size[1]

                out.save(outfile, format=ext[1:].lower())
        except IOError as e:
            messagebox.showerror("Error writing file",
                                 "File cannot be opened: %s" % e)
        except ValueError as e:
            messagebox.showerror("Unknown file extension",
                                 str(e))
        except:
            messagebox.showerror("Unexpected error", traceback.format_exc())

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

    # Load documents
    # TODO: Do this interactively.
    documents = load_documents(True)

    if hasattr(ttk, "Window"):
        root = ttk.Window()
    else:
        root = tk.Tk(className = "Ausweiskopie")

    foreground.instance = root

    try:
        root.wm_iconphoto(False, ImageTk.PhotoImage(ICON_IMAGE_COLORED))

        if '-editor' in sys.argv:
            root.wm_title(_('EDITOR'))
            m = EditorFrame(root)
        else:
            root.wm_title(_('APP_NAME'))
            m = MainFrame(root, documents)

        m.pack(expand=1, fill="both")

        root.mainloop()
    finally:
        if loop is not None:
            loop.quit()
