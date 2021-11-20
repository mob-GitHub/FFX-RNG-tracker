from ..data.constants import EquipmentType
from ..ui_functions import get_equipment_types
from .base_widgets import BaseWidget


class SeedInfo(BaseWidget):
    """Widget that shows general information
    about the seed.
    """

    def make_input_widget(self):
        return

    def get_input(self):
        data = [
            f'Seed number: {self.rng_tracker.seed}',
            get_equipment_types(50, 2),
        ]
        return '\n\n'.join(data)

    def print_output(self):
        input = self.get_input()
        self.output_widget.config(state='normal')
        self.output_widget.insert('end', input)
        self.output_widget.highlight_pattern(EquipmentType.ARMOR, 'blue')
        self.output_widget.config(state='disabled')