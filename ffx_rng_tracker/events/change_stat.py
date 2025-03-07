from dataclasses import dataclass

from ..data.actor import Actor, CharacterActor
from ..data.constants import Character, Stat
from .main import Event


@dataclass
class ChangeStat(Event):
    target: Actor
    stat: Stat
    stat_value: int

    def __post_init__(self) -> None:
        self.old_stat_value = self.target.stats[self.stat]
        self.stat_value = self._set_stat()

    def __str__(self) -> str:
        string = (f'Stat: {self.target} | {self.stat} | '
                  f'{self.old_stat_value} -> {self.stat_value}')
        return string

    def _set_stat(self) -> int:
        if not isinstance(self.target, CharacterActor):
            self.target.set_stat(self.stat, self.stat_value)
        elif self.target.character not in self.gamestate.bonus_aeon_stats:
            self.target.set_stat(self.stat, self.stat_value)
            if self.target.character is Character.YUNA:
                self.gamestate.calculate_aeon_stats()
        else:
            stats = self.gamestate.bonus_aeon_stats[self.target.character]
            old_bonus_stat = stats[self.stat]
            base = self.target.stats[self.stat] - old_bonus_stat
            new_bonus_stat = max(0, self.stat_value - base)
            stats[self.stat] = new_bonus_stat
            self.target.set_stat(self.stat, base + new_bonus_stat)
        return self.target.stats[self.stat]
