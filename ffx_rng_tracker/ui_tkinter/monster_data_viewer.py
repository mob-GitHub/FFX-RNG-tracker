import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..ui_abstract.monster_data_viewer import MonsterDataViewer
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget
from .tkinter_utils import create_command_proxy


class TkMonsterSelectionWidget(tk.Listbox):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('listvariable', tk.StringVar())
        kwargs.setdefault('highlightthickness', 0)
        super().__init__(parent, *args, **kwargs)
        self.bind('<<ThemeChanged>>', self.on_theme_changed)
        self._listvar: tk.StringVar = kwargs['listvariable']
        self._monster_names: list[str] = []

    def get_input(self) -> str:
        input_data = self.curselection()
        try:
            monster_index = input_data[0]
        # if there is nothing selected
        # curselection returns an empty tuple
        except IndexError:
            return ''
        return self._monster_names[monster_index]

    def set_input(self, text: str) -> None:
        old_selection, *monster_names = text.split('|')
        self._monster_names = monster_names
        self._listvar.set(monster_names)
        try:
            index = monster_names.index(old_selection)
        except ValueError:
            index = 0
        self.selection_clear(0, 'end')
        self.selection_set(index)
        self.activate(index)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self, {'activate'}, callback_func)

    def on_theme_changed(self, event: tk.Event) -> None:
        style = ttk.Style()
        fg = style.configure('.', 'foreground')
        bg = style.configure('.', 'background')
        fg_rgb = self.winfo_rgb(fg)
        # fg_rgb is a tuple of values from 0 to 0xffff
        if fg_rgb < (0xff, 0xff, 0xff):
            bg = '#ffffff'
        self.configure(foreground=fg, background=bg)


class TkMonsterDataViewer(ttk.Frame):
    """Widget used to display monster's data."""

    def __init__(self,
                 parent,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        frame = ttk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        monster_selection_widget = TkMonsterSelectionWidget(frame, width=30)
        monster_selection_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self, wrap='none')
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = MonsterDataViewer(
            configs=configs,
            monster_selection_widget=monster_selection_widget,
            search_bar=search_bar,
            output_widget=output_widget,
        )
