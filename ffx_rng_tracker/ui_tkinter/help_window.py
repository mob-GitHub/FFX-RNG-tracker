import tkinter as tk

from ..data.constants import UIWidget
from .tkinter_utils import show_message_box


def show_help_window(event: tk.Event) -> None:
    widget: tk.Misc | None = event.widget
    while True:
        if widget is None:
            return
        if hasattr(widget, 'tracker'):
            widget_name: UIWidget = widget.tracker.name
            break
        elif hasattr(widget, 'name'):
            widget_name: UIWidget = widget.name
            break
        else:
            widget = widget.master

    title = f'Help | {widget_name}'
    help_text = (f'The {widget_name} Widget '
                 f'{' '.join(HELP_TEXTS[widget_name].split('\n' + ' ' * 8))}')
    lines = [
        f'{help_text}\n',
        'Keyboard shortcuts:',
        '  F1: show this Help Window',
        '  F8: change Theme',
        '  Ctrl + S: Save Notes of current widget',
        '  Ctrl + Z: Undo (Input Text widgets only)',
        '  Ctrl + Y: Redo (Input Text widgets only)',
    ]
    show_message_box(widget, title=title, message='\n'.join(lines))


HELP_TEXTS: dict[UIWidget, str] = {
    UIWidget.SEED_INFO: """is used to load or change the current seed, and it
        shows some basic information about that seed.\n\nThe Input consists of
        an Entry where to put either Damage Values or a Seed Number, a
        Checkbutton that tells the program if you want to reload the Notes for
        all other Widgets, and a Button that when pressed will make the program
        parse your input and try to calculate a Seed from it; if there are any
        errors they will be shown right under the Button, otherwise the Seed
        will be sent to all other Widgets and their output text will be
        reprinted.\n\nThis Widget's Output consists of a readonly Text that
        will show the currently loaded Seed, a table of Equipment Types and a
        table of Status Application RNG Rolls for all Characters and Monsters.
        \n\nThe Equipment Types are the only part of Equipment Drops that will
        always be consistent no matter which Monster originated the Drop.\nThe
        Status Application RNG Rolls are useful because they are only used up
        when an Action tries to apply a Status Effect, making it possible to
        just keep track of these without having to track every other aspect of
        an Action to predict if a Status Application will fail, for example if
        the first Action that Tidus uses that will apply a Status Effect is an
        Attack while Stunning Steel is equipped, to predict if Slow will fail
        on a Target that has 20 Slow resistance, Roll 1 has to be lower than 30
        (50 Status Chance - 20 Status Resistance).
        """,
    UIWidget.DROPS: """is mainly used to track and predict Item, Equipment and
        Steal Drops, but it can also be useful to track AP and the Inventory.
        \n\nThe Input consists of a Search Box to search the Output and a Text
        where to write the list of Events the Tracker will use to produce the
        output text.\n\nThe Output is a readonly Text that will show the
        results of the Events in the same order as they were given.\n\nIt is
        necessary to list every Kill, Steal, Death and Bribe in the exact same
        order they happened in the game to be sure future predictions will be
        accurate. Some information can be omitted: which Characters get AP from
        a Kill and if that was an Overkill or not and which Character the Death
        has to attributed to is not RNG-related information.
        """,
    UIWidget.ENCOUNTERS: """is used to track and predict Encounters.\n\nThe
        Input consists of a Search Box to search the Output, a Sentry button
        that enables Initiative when applicable, a Padding button that enables
        padding to the output text, and a list of Encounter Sliders, each with
        it's Label that can also be clicked to tell the Output Widget to hide
        all the information above that Slider.\n\nThe Output is a readonly Text
        that will show the results of each Encounter Event, with each section
        that corresponds to a Slider being preceded by a text separator and the
        Label text.\n\nRandom Encounters roll Encounter RNG twice to determine
        Formation and Condition, other types (Forced, Simulation) only roll for
        Condition.\nSome Encounters overwrite the Condition with a
        predetermined one, for example most Forced ones will never be
        Ambush/Preemptive.\nEncounter Formation and Condition are only
        determined by the Zone and by the number of Encounter RNG Rolls used so
        far, meaning it is not necessary to keep track of the exact number of
        Encounters for each Zone, just the total amount of Random and
        Forced+Simulation Encounters (or the total amount of RNG rolls).
        """,
    UIWidget.STEPS: """Widget is used to track the number of Step RNG rolls and
        predict the number of Encounters.\n\nThe Input consists of a Search Box
        to search the Output, a Sentry button (unused), a Padding button that
        enables padding to the output text, and a list of Steps Sliders, each
        with it's Label that can also be clicked to tell the Output Widget to
        hide all the information above that Slider.\n\nThe Output is a readonly
        Text that will show a table with each row corresponding to a Slider in
        the Input Widget.\n\n
        """,
    UIWidget.ENCOUNTERS_PLANNER: """help text
        """,
    UIWidget.ENCOUNTERS_TABLE: """help text
        """,
    UIWidget.ACTIONS: """help text
        """,
    UIWidget.YOJIMBO: """help text
        """,
    UIWidget.MONSTER_DATA: """help text
        """,
    UIWidget.SEEDFINDER: """help text
        """,
    UIWidget.CONFIGS: """help text
        """,
}
