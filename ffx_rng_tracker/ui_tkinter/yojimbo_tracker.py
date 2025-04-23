from ..ui_abstract.yojimbo_tracker import YojimboTracker
from .tktracker import TkTracker


class TkYojimboTracker(TkTracker):
    tracker_type = YojimboTracker
