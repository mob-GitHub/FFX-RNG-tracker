from dataclasses import dataclass

from ..data.actor import MonsterActor
from ..data.constants import MonsterSlot
from ..data.monsters import Monster
from .main import Event


@dataclass
class MonsterSpawn(Event):
    monster: Monster
    slot: MonsterSlot
    ctb: int | None = None

    def __post_init__(self) -> None:
        self.new_monster = self._spawn_monster()
        self.ctb = self._calc_ctb()

    def __str__(self) -> str:
        return f'Spawn: {self.new_monster} with {self.ctb} CTB'

    def _spawn_monster(self) -> MonsterActor:
        actor = MonsterActor(self.monster, self.slot)
        if self.slot < len(self.gamestate.monster_party):
            self.gamestate.monster_party[self.slot] = actor
        else:
            self.gamestate.monster_party.append(actor)
        return actor

    def _calc_ctb(self) -> int:
        if self.ctb is None:
            ctb = self.new_monster.base_ctb * 3
        else:
            ctb = self.ctb
        ctb -= self.gamestate.ctb_since_last_action
        if ctb >= 0:
            self.new_monster.ctb = ctb
        else:
            self.gamestate.normalize_ctbs(ctb)
            self.gamestate.ctb_since_last_action += ctb
            self.new_monster.ctb = 0
        return self.new_monster.ctb
