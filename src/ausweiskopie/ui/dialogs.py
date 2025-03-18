"""
Provides open/save as dialogs. Uses the native (Desktop Portals) versions if
available, falls back to tkinter ones otherwise.
"""
import os
import tkinter
import warnings
from concurrent.futures import Future
from os import PathLike
from tkinter.filedialog import askopenfilename, asksaveasfilename
from typing import Union, Collection, Tuple, Optional, List, Sequence, Any, \
    Callable
from urllib.parse import unquote, urlparse

BUS_NAME_BASE = "org.freedesktop.portal"
BUS_OBJECT_PATH = "/org/freedesktop/portal/desktop"
BUS_CALL_BASE = BUS_NAME_BASE


def get_dbus_eventloop():
    from dbus.mainloop.glib import DBusGMainLoop

    return DBusGMainLoop()


_provide_dbus_interfaces: Optional[Callable[
    [Any], Optional[Tuple['dbus.Bus', 'dbus.Interface', 'dbus.Interface']]
]]
try:
    import dbus

    def _provide_dbus_interfaces(session_bus: dbus.Bus = None) -> Optional[Tuple['dbus.Bus', 'dbus.Interface', 'dbus.Interface']]:
        if session_bus is None:
            try:
                session_bus = dbus.SessionBus(mainloop=get_dbus_eventloop())
            except ImportError:
                raise NotImplementedError("Cannot get the eventloop!")
            except IOError:
                warnings.warn("Cannot connect to session bus. Is DBus running?")
                return None

        try:
            desktop = session_bus.get_object(
                BUS_NAME_BASE + ".Desktop", BUS_OBJECT_PATH
            )
        except IOError:
            warnings.warn("Cannot get Desktop object. Are the portals installed?")
            return None

        filechooser_iface = dbus.Interface(
            desktop,
            dbus_interface= BUS_CALL_BASE + ".FileChooser"
        )

        openuri_iface = dbus.Interface(
            desktop,
            dbus_interface= BUS_CALL_BASE + ".OpenUri"
        )
        return session_bus, filechooser_iface, openuri_iface


except ImportError:
    dbus = None
    _provide_dbus_interfaces = None


def _tk_filetypes_to_portals_filters(filetypes: Collection[Tuple[str, str]]) -> List[Tuple[str, List[Tuple['dbus.UInt32', str]]]]:
    return [
        (name, [(dbus.UInt32(0), pattern) for  pattern in filterstring.split()])
            for name, filterstring in filetypes
    ]


def _await_handle(path, bus) -> Tuple[int, Any]:
    f: Future[tuple] = Future()
    matcher = bus.add_signal_receiver(
        lambda _status, _result: f.set_result((_status, _result)),
        #print,
        dbus_interface=BUS_NAME_BASE + ".Request",
        path=path
    )
    status, result = f.result()
    matcher.remove()
    return status, result


def _create_dbus_options(
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
) -> dbus.Dictionary:
    options = dbus.Dictionary()
    options["modal"] = True
    if initialdir is not None:
        options["current_folder"] = str(initialdir).encode() + b"\0"
    else:
        options["current_folder"] = dbus.ByteArray(os.getcwdb() + b"\0")
    if filetypes:
        options["filters"] = _tk_filetypes_to_portals_filters(filetypes)
        options["current_filter"] = options["filters"][0]
    return options



def openfilename(
        *,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
        session_bus: Any = None
) -> Optional[str]:
    """Asks the user to open a file with a dialog."""
    try:
        return openfilename_desktopportals(
            filetypes=filetypes,
            initialdir=initialdir,
            title=title,
            parent=parent,
            session_bus=session_bus
        )
    except NotImplementedError:
        return openfilename_tk(
            filetypes=filetypes,
            initialdir=initialdir,
            parent=parent,
            title=title,
        )

def openfilename_desktopportals(
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
        session_bus: Optional['dbus.Bus'] = None
) -> Optional[str]:
    """Display an "open file" dialogue using XDG Desktop Portals."""
    if dbus is None:
        raise NotImplementedError("dbus (module) is not available")

    session_bus, dbus_filechooser, _ = _provide_dbus_interfaces(session_bus)
    options = _create_dbus_options(filetypes, initialdir)

    parent_id = ""
    if parent is not None:
        parent_id = f"x11:{parent.winfo_id()}"
    path = dbus_filechooser.OpenFile(parent_id, title or "", options)
    status, result = _await_handle(path, session_bus)
    if status != 0:
        return None
    uri: str = result["uris"][0]
    return unquote(urlparse(uri).path)


def openfilename_tk(
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
) -> Optional[str]:
    """Display an "open file" dialogue using Tkinter. Native dialogue on Windows and Mac, but not on Linux."""
    return askopenfilename(
        filetypes=filetypes,
        initialdir=initialdir,
        title=title,
        parent=parent,
    )


def savefileasname(
        defaultextension: Optional[str] = None,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        initialfile: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
        session_bus: Any = None
) -> Optional[Tuple[str, str]]:
    """Asks the user to open a file with a dialog."""
    try:
        return savefileasname_desktopportals(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=parent,
            session_bus=session_bus
        )
    except NotImplementedError:
        return savefileasname_tk(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=parent,
            title=title,
        )


def _get_current_extension(result) -> Optional[str]:
    if not result.get('current_filter'):
        return None
    if not result['current_filter'][1]:
        return None
    if not result['current_filter'][1][0]:
        return None
    if not result['current_filter'][1][0][1]:
        return None

    ext = os.path.splitext(result['current_filter'][1][0][1])[1]
    if ext:
        return ext
    return None

def savefileasname_desktopportals(
        defaultextension: Optional[str] = None,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        initialfile: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
        session_bus: Optional['dbus.Bus'] = None
) -> Optional[Tuple[str, str]]:
    """Provide a "Save file as" dialogue on Linux."""
    if dbus is None:
        raise NotImplementedError("dbus (module) is not available")

    session_bus, dbus_filechooser, _ = _provide_dbus_interfaces(session_bus)

    options = _create_dbus_options(filetypes, initialdir)
    if initialfile:
        options["current_file"] = initialfile

    parent_id = ""
    if parent is not None:
        parent_id = f"x11:{hex(parent.winfo_id())[2:]}"
    path = dbus_filechooser.SaveFile(parent_id, title or "", options)
    status, result = _await_handle(path, session_bus)
    if status != 0:
        return None
    uri: str = result["uris"][0]
    fn = unquote(urlparse(uri).path)
    _, extension = os.path.splitext(fn)
    if not extension:
        extension = _get_current_extension(result)
        # Do NOT extend the filename.
        # Yes, this is weird and not optimal
        # Tt would break flatpak portals,
        # as the filename *with extension* is not passed into the flatpak.
        if not extension and defaultextension is not None:
            extension = defaultextension
    return fn, extension


def savefileasname_tk(
        defaultextension: Optional[str] = None,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        initialfile: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
) -> Optional[Tuple[str, str]]:
    """Provide a "Save file as" dialogue with Tkinter."""
    filename = asksaveasfilename(
        defaultextension=defaultextension,
        filetypes=filetypes,
        initialdir=initialdir,
        initialfile=initialfile,
        title=title,
        parent=parent,
    )
    _, filetype = os.path.splitext(filename)
    if not filetype:
        filetype = defaultextension
    return filename, filetype
