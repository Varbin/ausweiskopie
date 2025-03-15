import tkinter
import traceback
from tkinter import ttk, messagebox
from typing import Optional, Collection, Callable, Tuple, Dict, Any

from PIL import Image, ImageTk, UnidentifiedImageError

from ausweiskopie.editor.exporter import get_exporter, EXPORTERS
from ausweiskopie.editor.importer import IMPORTERS, get_importer, import_from_field_definition
from ausweiskopie.editor.model import FieldLocation
from ausweiskopie.redact import Field, Location, FieldDefinition, ALL_FIELD_DEFINITIONS
from ausweiskopie.resources import _
from ausweiskopie.ui import savefileasname
from ausweiskopie.ui.dialogs import openfilename


def get_fields() -> Collection[Field]:
    fields = []
    for field in Field:
        fields.append(field)
    return fields


def get_known_field_definitions() -> Collection[Tuple[str, FieldDefinition]]:
    field_definitions = []
    for key, value in ALL_FIELD_DEFINITIONS.items():
        field_definitions.append((key, value))
    return sorted(field_definitions, key=lambda f: f[0])


class EditorFrame(ttk.Frame):
    def __init__(self, root):
        super(EditorFrame, self).__init__(root)

        editor = ImageEditor(self, image=None)
        editor.pack(fill=tkinter.BOTH, expand=True)

        # Status Bar
        self.status_var = status_var = tkinter.StringVar()
        status_var.set(_('EDITOR_STATUS_READY'))
        status_bar = tkinter.Label(root, textvariable=status_var, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)
        status_bar.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        ## MENU
        all_fields = get_fields()
        all_fields_with_labels = sorted([(_(field), field) for field in all_fields], key=lambda x: x[0])

        menubar = tkinter.Menu(self)

        # File Menu
        file_menu = tkinter.Menu(menubar, tearoff=0)
        file_menu.add_command(label=_('EDITOR_MENU_OPEN_IMAGE'), accelerator='Ctrl+O', command=editor.open_image)
        file_menu.add_separator()

        import_menu = tkinter.Menu(menubar, tearoff=0)
        for key, importer in IMPORTERS.items():
            import_menu.add_command(label=_(importer.get_import_label()), command=editor.import_from(key))
        file_menu.add_cascade(label=_('EDITOR_MENU_IMPORT_LAYOUT'), menu=import_menu)

        import_from_code_menu = tkinter.Menu(menubar, tearoff=0)
        for name, value in get_known_field_definitions():
            import_from_code_menu.add_command(label=name, command=editor.import_from_code(value))
        file_menu.add_cascade(label=_('EDITOR_MENU_IMPORT_LAYOUT_FROM_CODE'), menu=import_from_code_menu)

        export_menu = tkinter.Menu(menubar, tearoff=0)
        for key, exporter in EXPORTERS.items():
            export_menu.add_command(label=_(exporter.get_export_label()), command=editor.export_as(key))

        file_menu.add_cascade(label=_('EDITOR_MENU_EXPORT_LAYOUT'), menu=export_menu)
        file_menu.add_separator()
        file_menu.add_command(label=_('EDITOR_MENU_EXIT'), accelerator='Ctrl+Q', command=root.quit)
        menubar.add_cascade(label=_('EDITOR_MENU_FILE'), menu=file_menu, underline=0)

        # Edit Menu
        edit_menu = tkinter.Menu(menubar, tearoff=0)

        redefine_field_menu = tkinter.Menu(menubar, tearoff=0)
        for field_label, field in all_fields_with_labels:
            redefine_field_menu.add_command(label=field_label, command=editor.redefine_field(field))

        edit_menu.add_cascade(label=_('EDITOR_MENU_REDEFINE_FIELD'), menu=redefine_field_menu, underline=0)
        edit_menu.add_command(label=_('EDITOR_MENU_DELETE_FIELD'), accelerator='Delete', command=editor.delete_selected_field)
        edit_menu.add_separator()
        edit_menu.add_command(label=_('EDITOR_MENU_CLEAR_ALL_FIELDS'), accelerator='Ctrl+Delete', command=editor.clear_all_fields)
        menubar.add_cascade(label=_('EDITOR_MENU_EDIT'), menu=edit_menu, underline=0)

        # Field Menu
        add_field_menu = tkinter.Menu(menubar, tearoff=0)
        for field_label, field in all_fields_with_labels:
            add_field_menu.add_command(label=field_label, underline=0, command=editor.define_field(field))
        add_field_menu.add_separator()
        add_field_menu.add_command(label=_('EDITOR_MENU_CANCEL_DEFINE'), command=editor.define_field(None))
        menubar.add_cascade(label=_('EDITOR_MENU_DEFINE_FIELD'), menu=add_field_menu, underline=0)

        # Attach menu to window
        root.config(menu=menubar)
        root.bind_all("<Control-o>", lambda _: editor.open_image())
        root.bind_all("<Control-q>", lambda _: root.quit())
        root.bind_all("<Control-Delete>", lambda _: editor.clear_all_fields())

    def update_status(self,
                      status: Optional[str],
                      format_map: Optional[Dict[str, Any]] = None) -> None:
        if status:
            if format_map:
                self.status_var.set(_(status).format_map(format_map))
            else:
                self.status_var.set(_(status))
        else:
            self.status_var.set(_('EDITOR_STATUS_READY'))


class ImageEditor(ttk.Frame):
    def __init__(self, root: EditorFrame, image):
        super(ImageEditor, self).__init__(root)
        self.root = root

        # Load Image
        self.image = Image.new('RGBA', (800, 800), (255, 255, 255, 255))
        self.image.thumbnail((800, 800))
        self.tk_image = ImageTk.PhotoImage(self.image)

        # Canvas Setup
        canvas_group = ttk.LabelFrame(self, text=_('EDITOR_GROUP_MAIN_FIELD'))
        self.canvas = tkinter.Canvas(canvas_group, width=800, height=800)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        canvas_group.grid(row=0, column=0, sticky="nsw")

        # Display Image
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # Field Selection
        self.current_field: Optional[Field] = None
        self.selected_field: Optional[int] = None

        # Selection Listbox
        selection_group = ttk.LabelFrame(self, text=_('EDITOR_GROUP_FIELD_LIST'))
        self.selections = tkinter.Listbox(selection_group, selectmode=tkinter.BROWSE, width=50)
        self.selections.pack(fill=tkinter.BOTH, expand=True)
        self.selections.bind("<<ListboxSelect>>", self._highlight_field)
        self.selections.bind("<Delete>", self._delete_field)
        self._stored_fields: list[FieldLocation] = []

        selection_group.grid(row=0, column=1, sticky="news")

        # Rectangle Variables
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Bind Mouse Events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.canvas.bind("<Button-3>", self._on_mouse_right_click)

    def _on_mouse_press(self, event):
        """Start drawing a rectangle."""
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", width=2)
        self._update_position_labels(event)

    def _on_mouse_drag(self, event):
        """Update the rectangle's size while dragging."""
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
        self._update_position_labels(event)

    def _on_mouse_release(self, event):
        """Finalize the rectangle."""
        if self.current_field is None:
            self.canvas.delete(self.rect)
            return

        location = calculate_selection_location(
            (self.image.width, self.image.height),
            (self.start_x, self.start_y),
            (event.x, event.y),
        )
        record = FieldLocation(location=location,
                               field=self.current_field,
                               rect_id=self.rect)

        self._stored_fields.append(record)
        self.selections.insert(tkinter.END, f"{record}")

        self.current_field = None

        self.root.update_status('EDITOR_STATUS_DEFINED_FIELD', { 'field': _(record.field), 'location': record.location })

    def _highlight_field(self, _ev):
        """Highlight the selected rectangle in the listbox."""
        if self.selected_field:
            self.canvas.delete(self.selected_field)

        selection = self.selections.curselection()
        if not selection:
            return

        index = selection[0]
        selected_field = self._stored_fields[index]

        abs_start, abs_end = calculate_absolute_selection_location(
            (self.image.width, self.image.height),
            selected_field.location,
        )

        self.selected_field = self.canvas.create_rectangle(
            abs_start[0], abs_start[1],
            abs_end[0], abs_end[1],
            fill="green",
        )

        self.root.update_status('EDITOR_STATUS_HIGHLIGHTED_FIELD', { 'field': _(selected_field.field), 'location': selected_field.location })

    def _delete_field(self, _ev):
        selection = self.selections.curselection()
        if not selection:
            return

        index = selection[0]
        selected_field = self._stored_fields[index]
        if not selected_field.rect_id:
            return

        self.canvas.delete(selected_field.rect_id)
        if self.selected_field:
            self.canvas.delete(self.selected_field)

        self._stored_fields.pop(index)
        self.selections.delete(index)

        self.root.update_status('EDITOR_STATUS_DELETED_FIELD', { 'field': _(selected_field.field), 'location': selected_field.location })

    def _on_mouse_right_click(self, _):
        self.open_image()

    def define_field(self, field: Optional[Field]) -> Callable:
        def _fn():
            self.current_field = field
            if field:
                self.root.update_status('EDITOR_STATUS_DRAG_TO_DEFINE', {'field': _(field)})
            else:
                self.root.update_status(None)

        return _fn

    def redefine_field(self, field: Field) -> Callable:
        def _fn():
            selection = self.selections.curselection()
            if not selection:
                self.root.update_status('No field selected to redefine')
                return

            index = selection[0]
            selected_field = self._stored_fields[index]
            selected_field.field = field
            self.selections.delete(index)
            self.selections.insert(index, f'{selected_field}')

            self.root.update_status(f'Redefined field as "{_(field)}" at location ({selected_field.location})')

        return _fn

    @property
    def fields(self) -> list[FieldLocation]:
        return self._stored_fields

    @fields.setter
    def fields(self, fields: list[FieldLocation]):
        self.clear_all_fields()

        self._stored_fields = fields
        self._redraw_fields()

        self.selections.insert(tkinter.END, *[f'{f}' for f in fields])

    def import_from(self, import_type: str):
        def _fn():
            importer = get_importer(import_type)
            if not importer:
                return

            infile = openfilename(
                filetypes=importer.get_supported_file_extensions(),
                parent=self.winfo_toplevel(),
            )
            if not infile:
                return

            with open(infile, 'r', encoding='utf-8') as infile:
                file_content = infile.read()

            self.fields = importer.import_layout(file_content)
            self.root.update_status('EDITOR_STATUS_LOADED_LAYOUT', {'count': len(self.fields)})

        return _fn

    def import_from_code(self, field_def: FieldDefinition):
        def _fn():
            self.fields = import_from_field_definition(field_def)
            self.root.update_status('EDITOR_STATUS_LOADED_LAYOUT', {'count': len(self.fields)})

        return _fn

    def export_as(self, export_type: str):
        def _fn():
            exporter = get_exporter(export_type)
            if not exporter:
                return

            outfile, outfile_ext = savefileasname(
                defaultextension=exporter.get_default_file_extension(),
                filetypes=exporter.get_supported_file_extensions(),
                parent=self.winfo_toplevel(),
            )
            if not outfile:
                return

            payload = exporter.export(self._stored_fields)
            with open(outfile, 'w', encoding='utf-8') as f:
                f.write(payload)

            self.root.update_status('EDITOR_STATUS_EXPORTED_LAYOUT', {'outfile': outfile, 'exporter': _(exporter.get_export_label())})

        return _fn

    def delete_selected_field(self):
        self._delete_field(None)

    def clear_all_fields(self):
        for record in self._stored_fields:
            if record.rect_id:
                self.canvas.delete(record.rect_id)

        count = len(self._stored_fields)
        self._stored_fields = []
        self.selections.delete(0, tkinter.END)

        if self.selected_field:
            self.canvas.delete(self.selected_field)

        self.root.update_status('EDITOR_STATUS_CLEARED_FIELDS', { 'count': count })

    def open_image(self):
        filename = openfilename(filetypes=[
            ("Common image formats",
             "*.gif *.jpg *.jpeg *.jfiff *.png *.tiff *.webp")
        ], parent=self.winfo_toplevel())
        if not filename:
            return
        self._load_image_file(filename)

    def _load_image_file(self, filename: str):
        try:
            with open(filename, mode="rb") as image_file:
                img = Image.open(image_file)
                img.load()
            self.image = img.convert("RGB").copy()
            self.image.thumbnail((800, 800))

            self.tk_image = ImageTk.PhotoImage(self.image)

            self.canvas.delete(tkinter.ALL)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            self._redraw_fields()
            self.root.update_status('EDITOR_STATUS_LOADED_IMAGE', {'filename': filename})
        except UnidentifiedImageError as e:
            messagebox.showerror("Unknown image format",
                                 "The format of the image is unknown: %s" % e)
        except IOError as e:
            messagebox.showerror("Error reading file",
                                 "File cannot be opened: %s" % e)
        except:
            messagebox.showerror("Unexpected error", traceback.format_exc())

    def _update_position_labels(self, event):
        if not self.current_field:
            self.root.update_status('EDITOR_STATUS_NO_FIELD_SELECTED')
            return

        location = calculate_selection_location(
            (self.image.width, self.image.height),
            (self.start_x, self.start_y),
            (event.x, event.y) if event else (0, 0),
        )
        self.root.update_status('EDITOR_STATUS_RELEASE_TO_DEFINE_FIELD', { 'field': _(self.current_field), 'location': location })

    def _redraw_fields(self):
        if self.selected_field:
            self.canvas.delete(self.selected_field)

        for idx in range(len(self._stored_fields)):
            abs_start, abs_end = calculate_absolute_selection_location(
                (self.image.width, self.image.height),
                self._stored_fields[idx].location,
            )
            self._stored_fields[idx].rect_id = self.canvas.create_rectangle(
                abs_start[0], abs_start[1],
                abs_end[0], abs_end[1],
                outline="red", width=2)


def calculate_selection_location(image_size: Tuple[int, int],
                                 start_pos: Tuple[int, int],
                                 end_pos: Tuple[int, int]) -> Location:
    width, height = image_size
    start_x, start_y = start_pos
    end_x, end_y = end_pos

    # Calculate the relative coordinates, keeping them between 0 and 1
    rel_x1, rel_y1 = clamp(start_x / width), clamp(start_y / height)
    rel_x2, rel_y2 = clamp(end_x / width), clamp(end_y / height)

    # Ensure x1,y1 are top-left and x2,y2 are bottom-right
    final_x1 = min(rel_x1, rel_x2)
    final_y1 = min(rel_y1, rel_y2)
    final_x2 = max(rel_x1, rel_x2)
    final_y2 = max(rel_y1, rel_y2)

    return Location((final_x1, final_y1), (final_x2, final_y2))


def calculate_absolute_selection_location(image_size: Tuple[int, int],
                                          location: Location) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    width, height = image_size
    start_x, start_y = location.top_left
    end_x, end_y = location.bottom_right

    abs_x, abs_y = start_x * width, start_y * height
    abs_x2, abs_y2 = end_x * width, end_y * height

    return (abs_x, abs_y), (abs_x2, abs_y2)


def clamp(value, value_min=0, value_max=1):
    return min(max(value, value_min), value_max)
