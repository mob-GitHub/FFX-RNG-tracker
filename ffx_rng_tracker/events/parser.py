from ..errors import EventParsingError
from ..gamestate import GameState
from .comment import Comment
from .main import Event
from .parsing_functions import USAGE, ParsingFunction


class EventParser:
    """Helper class used to convert strings to events."""

    def __init__(self, gamestate: GameState) -> None:
        self.gamestate = gamestate
        self.parsing_functions: dict[str, ParsingFunction] = {}
        self.macros: dict[str, str] = {}

    def apply_macros(self, text: str) -> str:
        """Replace keys found in the self.macros dict with their values."""
        text = f'\n{text}\n'
        for name, macro in self.macros.items():
            text = text.replace(f'\n/macro {name}\n', f'\n{macro}\n')
        text = text[1:-1]
        return text

    def parse_to_string(self, text: str) -> str:
        return '\n'.join([str(e) for e in self.parse(text)])

    def parse(self, text: str) -> list[Event]:
        """Parse through the input text and returns a list of events."""
        text = self.apply_macros(text)

        lines = text.splitlines()
        events = []
        multiline_comment = False
        for i, line in enumerate(lines):
            if line.startswith('/*'):
                multiline_comment = True
            if multiline_comment:
                if line.endswith('*/'):
                    multiline_comment = False
                events.append(Comment(self.gamestate, f'# {line}'))
                continue

            if line == '/repeat' or line.startswith('/repeat '):
                _, *rest = line.split()
                try:
                    times = min(max(1, int(rest[0])), 5000)
                except (IndexError, ValueError):
                    times = 1
                try:
                    n_of_lines = min(max(1, int(rest[1])), 5000 // times)
                except (IndexError, ValueError):
                    n_of_lines = 1
                for _ in range(times):
                    for j in range(min(i, n_of_lines)):
                        lines.insert(i + 1, lines[i - 1 - j])

            event = self.parse_line(line)
            events.append(event)
        return events

    def parse_line(self, line: str) -> Event:
        """Parse the input line and returns an event."""
        words = line.lower().split()
        if not words or line.startswith('#'):
            return Comment(self.gamestate, line)
        elif line == '/macro' or line.startswith('/macro '):
            macro_names = ', '.join([f'"{m}"' for m in self.macros])
            text = f'Error: Possible macros are {macro_names}'
            return Comment(self.gamestate, text)
        elif line.startswith('/'):
            return Comment(self.gamestate, f'Command: {line}')
        event_name, *params = words
        try:
            parsing_func = self.parsing_functions[event_name]
        except KeyError:
            return Comment(
                self.gamestate, f'Error: No event called "{event_name}"')
        try:
            return parsing_func(self.gamestate, *params)
        except EventParsingError as error:
            if not str(error):
                usage = USAGE.get(parsing_func, ['No usage found'])[0]
                error = f'Usage: {usage}'
            return Comment(self.gamestate, f'Error: {error}')
