"""
In this module, helper functions for
"""
from concurrent.futures import Future
from functools import wraps
from queue import Empty, SimpleQueue
from threading import Thread, get_ident
from tkinter import Tk
from typing import Callable, Optional


class TkThread:
    """
    Threads decorated by this class will be executed in the thread of a Tk
    instance. Always register a Tk instance in the thread it was created in,
    otherwise a deadlock can occur if calling a wrapped function from the main
    thread. Wrapped functions called from the ui thread are always executed
    synchronously.
    """

    _queue: SimpleQueue
    _instance: Tk
    registered: bool
    poll_ms: int  #: Interval for polling for
    main_tid: int  #: The thread id of the main "ui" thread.

    def __init__(self, instance: Optional[Tk] = None, poll_ms: int = 250):
        self._queue = SimpleQueue()
        self.registered = False
        self.instance = instance
        self.poll_ms = poll_ms
        self.main_tid = get_ident()

    @property
    def instance(self) -> Optional[Tk]:
        return self._instance

    @instance.setter
    def instance(self, instance: Optional[Tk]):
        if self.registered:
            raise ValueError("Instance already set!")

        if instance is None:
            return

        self._instance = instance
        self._instance.after(self.poll_ms, self._schedule)
        self.registered = True

    def spawn(self):
        """Fetches a called function."""
        function: Callable
        args: tuple
        kwargs: dict
        future: Future

        try:
            function, args, kwargs, future = self._queue.get_nowait()
        except Empty:
            return

        # Future has been cancelled.
        if not future.set_running_or_notify_cancel():
            return

        try:
            result = function(*args, **kwargs)
        except Exception as e:
            future.set_exception(e)
        else:
            future.set_result(result)

    def _schedule(self):
        self._instance.after(self.poll_ms, self._schedule)
        self.spawn()

    def __call__(self, func: Callable):
        @wraps(func)
        def inner(*args, **kwargs) -> Future:
            future = Future()

            # If executed from the main thread, call synchronously to avoid
            # deadlocks.
            if get_ident() == self.main_tid or not self.registered:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    future.set_exception(e)
                else:
                    future.set_result(result)

            else:
                self._queue.put_nowait((func, args, kwargs, future))

            return future

        return inner


foreground = TkThread()


class Background(Thread):
    """
    Run a function in the background and fulfill a future after completion.
    """
    _future: Future

    def __init__(self, function: Callable, args: tuple, kwargs: dict,
                 future: Future):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._future = future

    def run(self) -> None:
        if not self._future.set_running_or_notify_cancel():
            return

        try:
            result = self.function(*self.args, **self.kwargs)
        except Exception as e:
            self._future.set_exception(e)
        else:
            self._future.set_result(result)


def background(func: Callable):
    """
    Functions decorated by this function will be executed in a freshly spawned
    thread.
    """
    @wraps(func)
    def inner(*args, **kwargs) -> Future:
        future = Future()
        Background(func, args, kwargs, future).start()
        return future

    return inner
