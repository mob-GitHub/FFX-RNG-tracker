import threading
import tkinter as tk
from queue import Queue
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

        self.dvs_entry = ttk.Entry(self.frame, textvariable=self.input_widget.damage_values)
        self.dvs_entry.pack(fill='x')

        self.button = ttk.Button(self.frame, text='Search Seed')
        self.button.pack()

        self.button.configure(command=self.find_seed_in_another_thread)

        self.progressbar = ttk.Progressbar(self.frame, mode='determinate')
        self.progressbar.pack(fill='x')

    def find_seed_in_another_thread(self) -> None:
        self.button.configure(state='disabled')
        self.input_widget.text.config(state='disabled')
        self.dvs_entry.config(state='disabled')
        self.progressbar.config(mode='indeterminate')
        self.progressbar.start()

        queue = Queue()

        def put_seed_in_queue() -> None:
            queue.put(self.tracker.find_seed())

        threading.Thread(target=put_seed_in_queue, daemon=True).start()

        def check_for_found_seed() -> None:
            if queue.empty():
                self.after(1000, check_for_found_seed)
                return
            self.progressbar.stop()
            self.progressbar.config(mode='determinate')
            self.dvs_entry.config(state='normal')
            self.input_widget.text.config(state='normal')
            self.button.configure(state='normal')
            self.tracker.print_found_seed(queue.get())

        check_for_found_seed()
