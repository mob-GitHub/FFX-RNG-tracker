from ..ui_abstract.actions_tracker import ActionsTracker
from .tktracker import TkTracker


class TkActionsTracker(TkTracker):
    tracker_type = ActionsTracker
