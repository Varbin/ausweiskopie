"""
Image import editor
"""
from collections.abc import Callable
from tkinter import Tk, Canvas, Event, Widget, StringVar, HORIZONTAL, \
    DoubleVar, IntVar

try:
    import ttkbootstrap as ttk
except ImportError:
    from tkinter import ttk
from tkinter.simpledialog import Dialog
from typing import Tuple, List, NamedTuple, Optional, cast, Any

from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance, ImageOps

from ..resources import get_string as _, get_resource
from ..resources import dimensions

CORNERS = Tuple['Corner', 'Corner', 'Corner', 'Corner']

import numpy

class Corner(NamedTuple):
    """A corner of a polygon."""
    x: int
    y: int

    SIZE = 30

    @property
    def corners(self) -> Tuple[int, int, int, int]:
        """Coordinates of corners around the center."""
        return self.x - self.SIZE // 2, self.y - self.SIZE // 2, self.x + self.SIZE // 2, self.y + self.SIZE // 2

    def hit(self, x, y):
        """Check if a coordinate pair is in the corner."""
        return (
                self.x - self.SIZE // 2 < x < self.x + self.SIZE // 2 and
                self.y - self.SIZE // 2 < y < self.y + self.SIZE // 2
        )


class Selector(Canvas):
    """Select a square on the image."""
    _rect: int = 0
    _polygon: int = 0
    _corners: List[Tuple[int, Corner]] = [(0, Corner(0, 0)) for i in range(4)]

    _start_x: int
    _start_y: int
    _active_corner: Optional[int] = None
    onupdate: Callable[[Optional[CORNERS]], Any] = None

    _image: Optional[Image.Image] = None
    _image_ref: int = 0

    def __init__(self,
                 parent: Widget,
                 width: int=600,
                 height: int=800,
                 *,
                 initial: Optional[CORNERS] = None,
                 image: Image.Image = None,
                 onupdate: Callable[[Optional[CORNERS]], Any] = lambda _: None,
                 ):
        super().__init__(parent, width=width, height=height)
        self._width, self._height = width, height

        if initial is not None:
            self._corners = []
            for corner in initial:
                self._corners.append(
                    (self.create_rectangle(corner.corners), corner)
                )

        self.bind("<ButtonPress-1>", self.onmousepress)
        self.bind("<B1-Motion>", self.onmousedrag)
        self.bind("<ButtonRelease-1>", self.onmouserelease)
        self.bind("<Motion>", self.onhover)

        self.onupdate = onupdate
        self.image = image

    def clear(self):
        self._delete_rect()
        self._delete_polygon()
        self._delete_corners()

    @property
    def selection(self) -> Optional[CORNERS]:
        if not all(ref for (ref, _) in self._corners):
            return None
        result = tuple(
            Corner(
                min(max(0, corner.x), self._width),
                min(max(0, corner.y), self._height)
            ) for (_, corner) in self._corners)
        return cast(CORNERS, result)

    @property
    def image(self) -> Optional[Image.Image]:
        return self._image

    @image.setter
    def image(self, image: Optional[Image.Image]):
        self._image = image
        if self._image_ref:
            self.delete(self._image_ref)
        if image is None:
            return
        image.thumbnail((self._width, self._height))
        self._tk_image = ImageTk.PhotoImage(image)
        self._image_ref = self.create_image(
            0, 0, anchor="nw", image=self._tk_image
        )

    def _delete_rect(self):
        if self._rect:
            self.delete(self._rect)

    def _delete_polygon(self):
        if self._polygon:
            self.delete(self._polygon)

    def _delete_corners(self):
        for i, (ref, corner) in enumerate(self._corners):
            if ref:
                self.delete(ref)
                self._corners[i] = (0, Corner(0, 0))

    def _draw_polygon(self):
        if self._polygon != 0:
            self.delete(self._polygon)
        self._polygon = self.create_polygon(
            tuple(corner for (_, corner) in self._corners),
            fill="",
            outline="blue",
        )

    def _find_corner(self, x, y) -> Optional[int]:
        for i, (ref, corner) in enumerate(self._corners):
            if not ref:
                continue
            if corner.hit(x, y):
                return i
        return None

    def onhover(self, event: Event):
        i = self._find_corner(event.x, event.y)
        if i is None:
            self.config(cursor="crosshair")
            return
        cursor = ["top_left", "bottom_left", "bottom_right", "top_right"][i]
        self.config(cursor = f"{cursor}_corner")

    def onmousepress(self, event: Event):
        active_corner = self._find_corner(event.x, event.y)
        if active_corner is not None:
            self._active_corner = active_corner
            return

        self._delete_rect()
        self._delete_polygon()
        self._delete_corners()
        self._start_x, self._start_y = event.x, event.y
        self._rect = self.create_rectangle(
            self._start_x, self._start_y, event.x, event.y,
            outline="red", width=2
        )
        self.onupdate(self.selection)

    def onmousedrag(self, event: Event):
        if self._active_corner is not None:
            ref = self._corners[self._active_corner][0]
            _, new = self._corners[self._active_corner] = ref, Corner(event.x, event.y)
            self.coords(ref, new.corners)
            self._draw_polygon()
            return

        self.coords(
            self._rect, self._start_x, self._start_y, event.x, event.y
        )

    def onmouserelease(self, event: Event):
        if self._active_corner is not None:
            self._active_corner = None
            self.onupdate(self.selection)
            return

        tl = Corner(min(self._start_x, event.x), min(self._start_y, event.y))
        bl = Corner(min(self._start_x, event.x), max(self._start_y, event.y))
        br = Corner(max(self._start_x, event.x), max(self._start_y, event.y))
        tr = Corner(max(self._start_x, event.x), min(self._start_y, event.y))

        for i, corner in enumerate((tl, bl, br, tr)):
            ref = self.create_rectangle(corner.corners)
            self._corners[i] = (ref, corner)
        self._delete_rect()
        self._draw_polygon()

        self.onupdate(self.selection)


class ImageEditor(ttk.LabelFrame):
    _image = None
    _image_preview = None
    _sizes = (
        dimensions.Names.ID1, dimensions.Names.ID2, dimensions.Names.ID3,
        dimensions.Names.CR90
    )
    _thumbnail_size = (300, 200)

    def __init__(self, master, text):
        super().__init__(master, text=text)

        self._format = StringVar()

        self.settings = ttk.Frame(self)
        self.settings.grid(row=0, column=0, sticky="new")
        self.image_frame = ttk.Label(self)
        self.image_frame.grid(column=0, row=1, sticky="new")

        self.grid_columnconfigure(0, weight=1)
        self.settings.grid_columnconfigure(1, weight=1)

        pad = dict(padx=4, pady=4)

        ttk.Label(self.settings, text="Size") \
            .grid(column=0, row=0, sticky="nw", **pad)
        self.format = ttk.Combobox(
            self.settings, textvariable=self._format
        )
        self.format.configure(state="readonly")
        self.format["values"] = [
            _(size) for size in self._sizes
        ]
        self.format.current(0)
        self.format.grid(column=1, row=0, columnspan=2, sticky="new", **pad)

        ttk.Separator(self.settings, orient=HORIZONTAL) \
            .grid(column=0, row=1, columnspan=3, sticky="nwe", **pad)

        ttk.Label(self.settings, text="Flip") \
            .grid(column=0, row=2, sticky="nw", **pad)
        self._horizontal = IntVar(value=0)
        self._vertical = IntVar(value=0)
        frame = self._checkboxes(self.settings)
        frame.grid(column=0, columnspan=3, row=2, sticky="new", **pad)

        ttk.Label(self.settings, text="Brightness") \
            .grid(column=0, row=4, sticky="nw", **pad)
        self._brightness = IntVar(self, 10)
        ttk.Scale(
            self.settings, from_=0, to=20, orient=HORIZONTAL,
            variable=self._brightness, command=self.update
        ).grid(column=1, row=4, sticky="nwe", **pad)
        self.brightness_label = ttk.Label(self.settings)
        self.brightness_label.grid(column=2, row=4, **pad)

        ttk.Label(self.settings, text="Contrast") \
            .grid(column=0, row=5, sticky="nw", **pad)
        self._contrast = IntVar(self, 10)
        ttk.Scale(
            self.settings, from_=0, to=20, orient=HORIZONTAL,
            variable=self._contrast, command=self.update
        ).grid(column=1, row=5, sticky="nwe", **pad)
        self.contrast_label = ttk.Label(self.settings)
        self.contrast_label.grid(column=2, row=5, **pad)

        ttk.Label(self.settings, text="Colour") \
            .grid(column=0, row=6, sticky="nw", **pad)
        self._color = IntVar(self, 10)
        ttk.Scale(
            self.settings, from_=0, to=20, orient=HORIZONTAL,
            variable=self._color, command=self.update
        ).grid(column=1, row=6, sticky="nwe", **pad)
        self.color_label = ttk.Label(self.settings)
        self.color_label.grid(column=2, row=6, **pad)

        ttk.Label(self.settings, text="Sharpness") \
            .grid(column=0, row=7, sticky="nw", **pad)
        self._sharpness = IntVar(self, 10)
        ttk.Scale(
            self.settings, from_=0, to=20, orient=HORIZONTAL,
            variable=self._sharpness, command=self.update
        ).grid(column=1, row=7, sticky="nwe", **pad)
        self.sharpness_label = ttk.Label(self.settings)
        self.sharpness_label.grid(column=2, row=7, **pad)

        ttk.Separator(self.settings, orient=HORIZONTAL) \
            .grid(column=0, row=8, columnspan=3, sticky="nwe", **pad)

        self.update()
        self.image = None

    def _checkboxes(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        size = (24, 24)

        self._enhance = IntVar(value=0)

        ttk.Label(frame, text="Enhance:") \
            .grid(column=0, row=0, sticky="nw")
        self._enhance_img = ImageTk.PhotoImage(
            Image.open(get_resource('enhance.png')).resize(size))
        ttk.Checkbutton(
            frame, image=self._enhance_img, variable=self._enhance,
            command=self.update,
        ).grid(column=1, row=0, sticky="nw", padx=8)
        ttk.Label(frame, text="Flip:") \
            .grid(column=2, row=0, sticky="nw", padx=8)

        self._horizontal_img = ImageTk.PhotoImage(
            Image.open(get_resource('mirrorh.png')).resize(size))

        ttk.Checkbutton(
            frame, variable=self._horizontal, image=self._horizontal_img,
            command=self.update,
        ).grid(column=3, row=0, sticky="nw", padx=8)

        self._vertical_img = ImageTk.PhotoImage(
            Image.open(get_resource('mirrorv.png')).resize(size))
        ttk.Checkbutton(
            frame, text="Vertical", variable=self._vertical,
            image=self._vertical_img, command=self.update,
        ).grid(column=4, row=0, sticky="ne", padx=8)
        return frame

    def filter(self, image: Image.Image) -> Image.Image:
        if self._horizontal.get():
            image = ImageOps.flip(image)
        if self._vertical.get():
            image = ImageOps.mirror(image)
        if self._enhance.get():
            image = ImageOps.autocontrast(image, cutoff=0.01, preserve_tone=True)
        brightness = ImageEnhance.Brightness(image)
        image = brightness.enhance(self._brightness.get() / 10)
        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(self._contrast.get() / 10)
        colour = ImageEnhance.Color(image)
        image = colour.enhance(self._color.get() / 10)
        sharpness = ImageEnhance.Sharpness(image)
        image = sharpness.enhance(self._sharpness.get() / 10)
        return image

    def update(self, *args):
        self.color_label.configure(text=f"{self._color.get()/10:.1f}")
        self.brightness_label.configure(text=f"{self._brightness.get()/10:.1f}")
        self.contrast_label.configure(text=f"{self._contrast.get()/10:.1f}")
        self.sharpness_label.configure(text=f"{self._sharpness.get()/10:.1f}")

        image = self.image
        if image is None:
            return
        thumb = image.copy()
        thumb.thumbnail(self._thumbnail_size)
        enhanced = self.filter(thumb)
        self._image_tk = ImageTk.PhotoImage(enhanced)
        self.image_frame.configure(text="", image=self._image_tk)

    def clear(self):
        self.image = None

    @property
    def size(self) -> Tuple[int, int]:
        return dimensions.VALUES[self._sizes[self.format.current()]]

    @property
    def image(self) -> Optional[Image.Image]:
        return self._image

    @image.setter
    def image(self, image: Optional[Image.Image]):
        self._image = image
        if image is None:
            cr80 = dimensions.VALUES[dimensions.Names.ID1]
            image = Image.new('L', self.size, 'white')
            draw = ImageDraw.Draw(image)
            draw.line((0,0) + cr80, fill="black", width=4)
            draw.line((cr80[0], 0, 0, cr80[1]), fill="black", width=4)
            image.thumbnail(self._thumbnail_size)
            self._image_tk = ImageTk.PhotoImage(image)
            self.image_frame.configure(text="", image=self._image_tk)

        self.update()

    @property
    def output_image(self) -> Optional[Image.Image]:
        if (image := self.image) is None:
            return None
        return self.filter(image)


def find_coeffs(pa, pb):
    """
    Find coefficients for perspective transformation.
    From https://stackoverflow.com/a/14178717/4414003.
    """
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = numpy.matrix(matrix, dtype=float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


class Editor(Dialog):
    front: ImageEditor
    back: ImageEditor

    def __init__(self, parent, img: Image, side="front"):
        self.img = img
        self.side = StringVar(parent, side)
        super().__init__(parent, "Editor")

    def onupdate(self, corners: CORNERS):
        side = {
            "front": self.front,
            "back": self.back,
        }[self.side.get()]
        if corners is not None:
            w, h = side.size
            try:
                coeffs = find_coeffs(((0, 0), (0, h), (w, h), (w, 0)), corners)
            except numpy.linalg.LinAlgError:
                img = None
            else:
                img = self.img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs)
        else:
            img = None
        side.image = img

    def body(self, master):
        pad = dict(padx=4, pady=4, ipadx=4, ipady=4)
        select = ttk.LabelFrame(master, text="Select")
        select.grid(row=0, column=0, columnspan=1, sticky='new', **pad)
        ttk.Label(select, text=_("HELP_EDITOR")).grid(row=0, column=0, columnspan=2)
        selection = Selector(
            select, 600, 480,
            image=self.img, onupdate=self.onupdate,
        )
        selection.configure(background="white")
        selection.grid(row=1, column=0, rowspan=4, sticky='nw')
        right = ttk.Frame(select)
        right.grid(row=1, column=1, sticky='nw')
        ttk.Label(right, text="Side").grid(row=0, column=0, sticky='nw')
        ttk.Radiobutton(right, text="Front", value="front", variable=self.side).grid(row=1, column=0, sticky='nw')
        ttk.Radiobutton(right, text="Back", value="back", variable=self.side).grid(row=2, column=0, sticky='nw')
        self.side.trace_add('write', lambda *args: selection.clear())
        self.front = ImageEditor(master, "Front")
        self.front.grid(row=0, column=1, sticky='new', **pad)

        self.back = ImageEditor(master, "Back")
        self.back.grid(row=0, column=2, sticky='new', **pad)

        for i in range(2):
            master.grid_columnconfigure(i, weight=1)
            master.grid_rowconfigure(i, weight=1)

    def validate(self):
        result = self.getresult()
        ok = result != (None, None)
        if ok:
            self.result = result
        return ok

    def buttonbox(self):
        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default="active")
        if hasattr(ttk, "style"):
            w.configure(bootstyle="success")
        w.pack(side="left", padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        if hasattr(ttk, "style"):
            w.configure(bootstyle="danger")
        w.pack(side="left", padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def getresult(self):
        return self.front.output_image, self.back.output_image
