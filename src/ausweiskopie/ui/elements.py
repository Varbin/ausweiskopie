"""
UI elements.
"""
import tkinter
from datetime import datetime
import tkinter as tk
import traceback
from tkinter import messagebox
from tkinter import colorchooser

from PIL import ImageDraw

from .dialogs import openfilename
from .dnd import TkDND

try:
    import ttkbootstrap as ttk
except ImportError:
    from tkinter import ttk
    ttk.Text = tk.Text

from typing import Collection, Mapping, Optional

from PIL import Image, ImageTk, UnidentifiedImageError

from ..personalize import personalize
from ..redact import redact
from ..redact.definitions import FieldDefinition, Field
from ..resources import _

class DocumentFrame(ttk.LabelFrame):
    """Element to select a document picture and its type."""
    def __init__(self, root, title, default,
                 document_types: Mapping[str, FieldDefinition]):

        super(DocumentFrame, self).__init__(root)
        self.configure(text=title)

        self.picture = Picture(self, default)
        self.picture.pack(expand=1, fill="x", padx=8, pady=8)
        self.picture.callback = self.change

        self.document_types = document_types

        self._document_type = tk.StringVar()
        self._document_type.trace_add("write", self.change)

        self.document_selection = ttk.Combobox(
            self, textvariable=self._document_type
        )
        self.document_selection.configure(state="readonly")
        self.document_selection["values"] = tuple(
            sorted(document_types.keys())
        )
        self.document_selection.current(0)
        self.document_selection.pack(expand=1, fill="x", padx=8, pady=8)

    def change(self, *args, **kwargs):
        """Callback to show field marks."""
        _ = args
        _ = kwargs

        self.picture.preview = DocumentFrame.redact_and_personalize(
            self.picture.image,
            "",
            "white",
            "black",
            [],
            self.document_types[self._document_type.get()],
            False,
            True
        )

    @property
    def skip(self) -> bool:
        """Whether to skip this page."""
        return not self.document_types[self._document_type.get()]

    @staticmethod
    def redact_and_personalize(
            image: Image.Image,
            text: str,
            text_color: str,
            redact_color: str,
            redact_fields: Collection[Field],
            document_type: FieldDefinition,
            grayscale: bool = True,
            mark: bool = False,
            text_transparency: float = 0.5,
    ) -> Image.Image:
        """Redact and personalize any image."""
        if not document_type:
            img = Image.new("RGBA", image.size, "white")
            draw = ImageDraw.Draw(img)
            draw.line(((0, 0), img.size), "black", width=2)
            draw.line(((0, img.size[1]), (img.size[0], 0)), "black", width=2)
            return img

        img = image.copy()
        img = redact(
            img,
            redact_fields,
            document_type,
            False,
            redact_color,
        )

        if mark:
            img = redact(
                img,
                set(document_type.keys()) - set(redact_fields),
                document_type,
                True,
                "black"
            )

        img = personalize(img, grayscale, text, text_color, text_transparency,
                          data={
                             "today": datetime.now().strftime("%d.%m.%y")
                          })
        return img

    def apply(
            self,
            text: str,
            text_color: str,
            redact_color: str,
            redact_fields: Collection[Field],
            grayscale: bool = True,
            mark: bool = False,
            text_transparency: float = 0.5,
            preview=True,
    ):
        """Redact and personalize image."""
        new_image = DocumentFrame.redact_and_personalize(
            self.picture.image,
            text, text_color, redact_color, redact_fields,
            self.document_types[self._document_type.get()],
            grayscale,
            mark, text_transparency,
        )
        if preview:
            self.picture.preview = new_image
        return new_image


class Picture(ttk.Frame):
    _preview: Image.Image  # The displayed image.
    __preview_tk: ImageTk.PhotoImage
    _image: Image.Image  # The selected image.
    label: ttk.Label

    def __init__(self, root, default=None, limit=400, callback=None):
        super(Picture, self).__init__(root)
        self.label = ttk.Label(self, cursor="hand1")
        self.label.bind("<ButtonRelease-1>", self.onclick)

        self.limit = limit
        self.callback = callback

        if default is not None:
            if isinstance(default, Image.Image):
                self.image = default
            else:
                self.image = Image.open(default)
        self.label.pack(fill="both", expand=1)

        self._register_dnd()

    def _register_dnd(self):
        try:
            dnd = TkDND(self.winfo_toplevel())
        except tkinter.TclError:
            return

        dnd.drop_target_register(self.label, ["DND_Files"])
        dnd.bind(self.label, "<<Drop>>", self.ondrop)

    @property
    def image(self) -> Optional[Image.Image]:
        """Underlying image"""
        return self._image

    @image.setter
    def image(self, new_image: Image.Image):
        self._image = new_image
        self.preview = new_image
        if self.callback is not None:
            self.callback(self._image)

    @property
    def preview(self) -> Optional[Image.Image]:
        """Displayed image."""
        return self._preview

    @preview.setter
    def preview(self, new_preview: Image.Image):
        self._preview = new_preview.copy()
        self._preview.thumbnail((self.limit, self.limit))
        self.__preview_tk = ImageTk.PhotoImage(self._preview)
        self.label.configure(image=self.__preview_tk)
        self.label.image = self.__preview_tk

    def onclick(self, _):
        """Onclick handler."""
        filename = openfilename(filetypes=[
            ("Common image formats",
             "*.gif *.jpg *.jpeg *.jfiff *.png  *.tiff *.webp")
        ], parent=self.winfo_toplevel())
        if not filename:
            return
        self._load_image_file(filename)

    def ondrop(self, event):
        """Drop handler."""
        self._load_image_file(event.data[0])

    def _load_image_file(self, filename: str):
        try:
            with open(filename, mode="rb") as image_file:
                img = Image.open(image_file)
                img.load()
            self.image = img.convert("RGB")
        except UnidentifiedImageError as e:
            messagebox.showerror("Unknown image format",
                                 "The format of the image is unknown: %s" % e)
        except IOError as e:
            messagebox.showerror("Error reading file",
                                 "File cannot be opened: %s" % e)
        except:
            messagebox.showerror("Unexpected error", traceback.format_exc())


class Selection(ttk.Frame):
    def __init__(self, master, kv: Mapping[str, str], defaults: set[str],
                 columns=1):
        super(Selection, self).__init__(master)

        self.store = {}

        row, column = 0, 0

        self.grid_rowconfigure(row, weight=1)
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1)

        for display, value in kv.items():
            variable = tk.IntVar()
            if value in defaults:
                variable.set(1)
            btn = ttk.Checkbutton(
                self, text=display, variable=variable, onvalue=1, offvalue=0
            )
            btn.grid(row=row, column=column, padx=8, pady=8, sticky="WE")
            self.store[value] = variable

            column = (column + 1) % columns
            if not column:
                row += 1
                self.grid_rowconfigure(row, weight=1)

    def get_selections(self) -> Collection[str]:
        out = []
        for value, variable in self.store.items():
            if variable.get():
                out.append(value)
        return out


class ColorButton(ttk.Label):
    def __init__(self, master, default_color="#ff0000"):
        super().__init__(master, text=" "*8, background=default_color, cursor="hand1")
        self.bind("<ButtonRelease-1>", self.onclick)
        self.color = default_color

    def onclick(self, *args):
        _ = args
        html = colorchooser.askcolor(self.color)[1]
        if html is not None:
            self.configure(background=html)
            self.color = html


class MarkFrame(ttk.LabelFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._use_watermark = tk.IntVar(value=1)
        self._grayscale = tk.IntVar(value=1)
        self._percentage_value = 50
        self._percentage = tk.StringVar(value=str(self._percentage_value))
        self._percentage.trace_add("write", self._ensure_percentage)

        padding = {"padx": 8, "pady": 8}

        # Column 0
        ttk.Checkbutton(self, text=_("GRAYSCALE"),
                        variable=self._grayscale)\
            .grid(row=0, column=0, **padding)

        # Column 1 -> Inner frame
        watermark = ttk.LabelFrame(self, text=_("WATERMARK"))

        watermark.grid(row=0, column=1, **padding, sticky="WE")
        self.grid_columnconfigure(1, weight=1)

        # Column 1.0
        ttk.Checkbutton(watermark, text=_("WATERMARK"),
                        variable=self._use_watermark)\
            .grid(row=0, column=0, **padding, sticky="W")

        input_frame = ttk.Frame(watermark)
        ttk.Label(input_frame, text=_("COLOR"))\
            .grid(row=0, column=0, sticky="W",  **padding)
        ttk.Label(input_frame, text=_("TRANSPARENCY")) \
            .grid(row=1, column=0, sticky="W",  **padding)
        self.color_button = ColorButton(input_frame)
        self.color_button.grid(row=0, column=1,  **padding)
        ttk.Entry(input_frame, textvariable=self._percentage, width=4,
                  justify="right").grid(row=1, column=1,  **padding)
        input_frame.grid(row=2, column=0, **padding, sticky="W")

        # Column 1.1
        self.text_box = ttk.Text(watermark)
        self.text_box.tag_configure("center", justify="center")
        self.text_box.configure(
            height=len(_("COPY_TEXT").split("\n")),
            width=40,
        )
        self.text_box.insert("0.0", _("COPY_TEXT"))
        self.text_box.tag_add("center", "0.0", tk.END)
        self.text_box.grid(row=0, column=1, rowspan=4, sticky="WE", **padding)

        watermark.grid_columnconfigure(1, weight=1)

    @property
    def use_watermark(self) -> bool:
        return bool(self._use_watermark.get())

    @property
    def grayscale(self) -> bool:
        return bool(self._grayscale.get())

    @property
    def color(self) -> str:
        return self.color_button.color

    @property
    def text(self) -> str:
        return self.text_box.get("0.0", tk.END)

    @property
    def percentage(self) -> int:
        return self._percentage_value

    def _ensure_percentage(self, *args):
        new = self._percentage.get()
        if not new:
            self._percentage.set("0")
            return

        try:
            percentage = int(new)
        except ValueError:
            self._percentage.set(str(self._percentage_value))
            return

        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
        else:
            self._percentage_value = percentage
            return

        self._percentage.set(str(percentage))

