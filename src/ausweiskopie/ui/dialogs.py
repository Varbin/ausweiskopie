"""
Provides open/save as dialogs. Uses the native (Desktop Portals) versions if
available, falls back to tkinter ones otherwise.
"""
import io
import os
import threading
import tkinter
import warnings
from os import PathLike
from tkinter.filedialog import askopenfile, askopenfilename, asksaveasfilename
from typing import Union, Collection, Tuple, Optional, List, Sequence, Any
from concurrent.futures import Future
from urllib.parse import unquote, urlparse, urlencode, quote

BUS_NAME_BASE = "org.freedesktop.portal"
BUS_OBJECT_PATH = "/org/freedesktop/portal/desktop"
BUS_CALL_BASE = BUS_NAME_BASE


def get_dbus_eventloop():
    from dbus.mainloop.glib import DBusGMainLoop

    return DBusGMainLoop()


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
                return


        try:
            desktop = session_bus.get_object(
                BUS_NAME_BASE + ".Desktop", BUS_OBJECT_PATH
            )
        except IOError:
            warnings.warn("Cannot get Desktop object. Are the portals installed?")
            return

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
    f = Future()
    matcher = bus.add_signal_receiver(
        lambda status, result: f.set_result((status, result)),
        #print,
        dbus_interface=BUS_NAME_BASE + ".Request",
        path=path
    )
    status, result = f.result()
    matcher.remove()
    return status, result


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

    options = dbus.Dictionary()
    options["modal"] = True
    if initialdir is not None:
        options["current_folder"] = str(initialdir).encode() + b"\0"
    else:
        options["current_folder"] = dbus.ByteArray(os.getcwdb() + b"\0")
    if filetypes:
        options["filters"] = _tk_filetypes_to_portals_filters(filetypes)
        options["current_filter"] = options["filters"][0]

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
) -> Optional[io.FileIO]:
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


def savefileasname_desktopportals(
        defaultextension: Optional[str] = None,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        initialfile: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
        session_bus: Optional['dbus.Bus'] = None
) -> Optional[str]:
    """Provide a "Save file as" dialogue on Linux."""
    if dbus is None:
        raise NotImplementedError("dbus (module) is not available")

    session_bus, dbus_filechooser, _ = _provide_dbus_interfaces(session_bus)

    options = dbus.Dictionary()
    options["modal"] = True
    if initialdir is not None:
        options["current_folder"] = str(initialdir).encode()+b"\0"
    else:
        options["current_folder"] = dbus.ByteArray(os.getcwdb()+b"\0")
    if filetypes:
        options["filters"] = _tk_filetypes_to_portals_filters(filetypes)
        options["current_filter"] = options["filters"][0]
    if initialfile:
        options["current_file"] = initialfile

    parent_id = ""
    if parent is not None:
        parent_id = f"x11:{parent.winfo_id()}"
    path = dbus_filechooser.SaveFile(parent_id, title or "", options)
    status, result = _await_handle(path, session_bus)
    if status != 0:
        return None
    uri: str = result["uris"][0]
    return unquote(urlparse(uri).path)


def savefileasname_tk(
        defaultextension: Optional[str] = None,
        filetypes: Sequence[Tuple[str, str]] = (),
        initialdir: Union[str, PathLike, None] = None,
        initialfile: Union[str, PathLike, None] = None,
        title: Optional[str] = None,
        parent: Optional[tkinter.Tk] = None,
) -> Optional[str]:
    """Provide a "Save file as" dialogue with Tkinter."""
    return asksaveasfilename(
        defaultextension=defaultextension,
        filetypes=filetypes,
        initialdir=initialdir,
        initialfile=initialfile,
        title=title,
        parent=parent,
    )
