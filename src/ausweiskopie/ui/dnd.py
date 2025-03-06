"""
Minimal (external) drag and drop support for tkinter.

Author:     mmgp
License:    CC BY-SA 3.0
https://stackoverflow.com/a/14283431
"""

import tkinter
from typing import Callable, Any, Union, List, Tuple, Optional, Sequence


def _load_tkdnd(master: tkinter.Tk):
    version = master.tk.eval('package require tkdnd')
    master._tkdnd_loaded = True
    return version


class TkDND:
    """
    Wrapper of the TkDND library.
    """

    """
    %%
        Replaced with a single percent. 
    %A
        The current action of the drag/drop operation. 
    %a
        The action list supported by the drag source. 
    %b
        The mouse button that is pressed during a drag/drop operation. Note that always a single mouse button is reported as pressed, even if more than one mouse buttons are actually pressed. 
    %c
        The codes of the list of types supported by the drag source. All codes are in octal format and have the same order as the list of types obtained through the %t substitution. 
    %C
        The code (in octal format) of the current type of the drag and drop operation. 
    %CTT
        The list of types from the drop target type list that are common to the drag source type list. 
    %CST
        The list of types from the drag source type list that are common to the drop target type list. 
    %D
        The data that has been dropped. Under some platforms the data will be available before the drop has occured. The format of the data is the current type of the drop operation. 
    %e
        The name of the current virtual event. One of <>, <>, <>, <type>>, <>, <>, <>. 
    %L
        The list of types supported by the drag source. 
    %m
        The list of modifier keyboard keys that are pressed. Modifier keys are some special keys, like Shift, Control or Alt. Valid modifiers are "shift", "ctrl" and "alt". It is useful for binding scripts of drop target events to examine this list of modifiers, as it is quite usuall to change the action according to the state of some modifier keys. 
    %ST
        The list of types supported by the drag source. 
    %t
        The list of types supported by the drag source. 
    %T
        The current type of the drag and drop operation. 
    %TT
        The list of types supported by the drop target. 
    %W
        The window that the event is delivered to. 
    %X
        The mouse pointer x coordinate, relative to the root window. 
    %Y
        The mouse pointer y coordinate, relative to the root window.
        
    (Surround multi-letter arguments with {})
    """
    _subst_format = ("%A", "%b", "%C", "%D", "%e", "%m", "%T", "%W", "%X", "%Y", "%x", "%y")

    root: tkinter.Tk

    def __init__(self, root: tkinter.Tk):
        if not getattr(root, '_tkdnd_loaded', False):
            self.version = _load_tkdnd(root)
        self.root = root

    def drop_target_register(self, window: tkinter.Widget, type_list: Optional[list[str]] = (), button: Optional[int] = None):
        return self.root.tk.call("tkdnd::drop_target", "register", window,
                                 type_list, button)

    def drop_target_unregister(self, window: tkinter.Widget):
        return self.root.tk.call("tkdnd::drop_target", "unregister", window)

    def platform_specific_types(self, types: list[str]) -> list[str]:
        return self._split_list(self.root.tk.call("tkdnd::platform_specific_types", types))

    def platform_independent_types(self, types: list[str]) -> list[str]:
        return self._split_list(self.root.tk.call("tkdnd::platform_independent_types", types))

    def bind(self, what: tkinter.Widget, sequence: str, func: Union[str, Callable[[tkinter.Event], Any]], add: bool=False, needcleanup: bool=True) -> Union[str, Sequence[str]]:
        """Bind to given *DnD* event. The function is wrapped to an event will be passed."""
        if not isinstance(func, str):
            func = self._wrap_function(func, needcleanup)
            if add:
                func = f"+{func}"
        elif not func:
            return self._split_list(self.root.tk.call("bind", what))
        elif not func:
            return self.root.tk.call("bind", what, sequence)

        return self.root.tk.call("bind", what, sequence, func)

    @staticmethod
    def _get_int(element: Any, base: int = 10) -> Union[int, Any]:
        try:
            return str(int(element, base=base))
        except ValueError:
            return element

    def _split_list(self, element: str) -> List[str]:
        return self.root.tk.splitlist(element)

    def _wrap_function(self, callback: Callable[[tkinter.Event], Any], cleanup: bool=True) -> str:
        """Wraps a callable for Tcl, so it will be called with a single event object."""
        # Register returns a seemingly random function name, valid in Tcl
        # The callback will be called with the return value of the substitute function
        name = self.root.register(callback, self._substitute_function, cleanup)
        # Add arguments to the created function
        return f"{name} {' '.join(self._subst_format)}"

    def _name_to_widget(self, name: str) -> Union[str, tkinter.Widget]:
        try:
            return self.root.nametowidget(name)
        except KeyError:
            return name

    def _substitute_function(self, *args) -> Tuple[tkinter.Event]:
        """
        Retrieves individual arguments from a TkDND event and returns them as a singular tkinter.Event object.

        See the _subst_format property for details what is passed into *args.
        """
        if len(args) != len(self._subst_format):
            raise ValueError("Called with wrong number of arguments")

        # valid percent substitutions for DnD event types
        # (tested with tkdnd-2.8 on debian jessie):
        # <<DragInitCmd>> : %W, %X, %Y %e, %t
        # <<DragEndCmd>> : %A, %W, %e
        # <<DropEnter>> : all except : %D (always empty)
        # <<DropLeave>> : all except %D (always empty)
        # <<DropPosition>> :all except %D (always empty)
        # <<Drop>> : all
        A, b, C, D, e, m, T, W, X, Y, x, y  = args
        ev = tkinter.Event()
        ev.action = A
        ev.button = self._get_int(b)
        ev.code = self._get_int(C, 8)
        if isinstance(self._split_list(m), list):
            ev.state = "|".join(self._split_list(m) + f"Button{b}")
        else:
            mods = self._split_list(m)
            if b:
                mods.append(f"Button{b}")
            ev.state = "|".join(mods)

        ev.x = self._get_int(x)
        ev.y = self._get_int(y)
        ev.x_root = self._get_int(X)
        ev.y_root = self._get_int(Y)
        ev.type = T
        ev.data = D  # To splitlist!
        if "DND_Files" in self.platform_independent_types(T):
            ev.data = self._split_list(ev.data)
        ev.name = e
        ev.widget = ev.window = self._name_to_widget(W)
        # Will crash otherwise!
        ev.char = "??"
        ev.delta = 0

        return (ev,)
