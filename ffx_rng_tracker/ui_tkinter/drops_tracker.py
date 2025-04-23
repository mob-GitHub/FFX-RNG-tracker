from ..ui_abstract.drops_tracker import DropsTracker
from .tktracker import TkTracker


class TkDropsTracker(TkTracker):
    tracker_type = DropsTracker
