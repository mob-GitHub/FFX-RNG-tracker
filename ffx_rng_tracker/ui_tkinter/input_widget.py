import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from .base_widgets import ScrollableText
from .tkinter_utils import create_command_proxy, get_default_font


class TkInputWidget(ScrollableText):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('font', get_default_font())
        kwargs.setdefault('width', 40)
        kwargs.setdefault('undo', True)
        kwargs.setdefault('autoseparators', True)
        kwargs.setdefault('maxundo', -1)
        super().__init__(parent, *args, **kwargs)

    def get_input(self) -> str:
        return self.text.get('1.0', 'end')

    def set_input(self, text: str) -> None:
        self.set(text)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(
            self.text, {'insert', 'delete', 'replace'}, callback_func)


class TkDefaultTextEntry(ttk.Entry):

    def __init__(self,
                 parent,
                 default_text: str = '',
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.default_text = default_text
        self.on_focus_out()
        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)
        self.bind('<Return>', self.on_return)

    def get_input(self) -> str:
        if str(self.cget('state')) == 'readonly':
            return ''
        return self.get()

    def set_input(self, text: str) -> None:
        self.delete('0', 'end')
        self.insert('0', text)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(
            self, {'insert', 'delete', 'replace', 'Return'}, callback_func)

    def on_focus_in(self, event: tk.Event | None = None) -> None:
        if str(self.cget('state')) == 'readonly':
            self.config(state='normal')
            self.set_input('')

    def on_focus_out(self, event: tk.Event | None = None) -> None:
        if self.get() == '':
            self.set_input(self.default_text)
            self.config(state='readonly')

    def on_return(self, event: tk.Event | None = None) -> None:
        # will always raise a TclError but
        # it will be intercepted by the command proxy
        try:
            self.tk.call(str(self), 'Return')
        except tk.TclError:
            pass


class TkSearchBarWidget(TkDefaultTextEntry):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, 'Search...', *args, **kwargs)
