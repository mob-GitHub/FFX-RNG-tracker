import tkinter as tk
from tkinter import ttk
from typing import Literal

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.seedfinder import SeedFinder
from .input_widget import TkInputWidget
from .tktracker import TkTracker


class TkSeedFinderInputWidget(TkInputWidget):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.damage_values = tk.StringVar(self)

    def get_input(self) -> str:
        text = (f'{self.damage_values.get()}\n'
                f'///\n'
                f'{super().get_input()}'
                )
        return text


class TkSeedFinder(TkTracker):
    tracker_type = SeedFinder
    input_widget_type = TkSeedFinderInputWidget

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 orient: Literal['vertical', 'horizontal'] = 'horizontal',
                 ) -> None:
        super().__init__(parent, parser, configs, orient)
        self.tracker: SeedFinder
        self.input_widget: TkSeedFinderInputWidget

        ttk.Label(self.frame, text='Actions').pack(after=self.search_bar)

        ttk.Label(self.frame, text='Damage values').pack()

        ttk.Entry(self.frame, textvariable=self.input_widget.damage_values).pack(fill='x')

        button = ttk.Button(self.frame, text='Search Seed')
        button.pack()

        button.configure(command=self.tracker.find_seed)
