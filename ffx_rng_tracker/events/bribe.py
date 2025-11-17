from dataclasses import dataclass
from math import sqrt

from ..configs import Configs
from ..data.actor import CharacterActor, MonsterActor
from ..data.constants import GameVersion, KillType, Stat, Status
from ..data.items import ItemDrop
from .kill import Kill
from .main import Event


@dataclass
class BribeDrop(Kill):

    def __post_init__(self) -> None:
        self.kill_type = KillType.NORMAL
        super().__post_init__()

    def _get_item_1(self) -> ItemDrop | None:
        return self.monster.bribe.item

    def _get_item_2(self) -> None:
        return


@dataclass
class BribeAction(Event):
    character: CharacterActor
    monster: MonsterActor
    gil: int

    def __post_init__(self) -> None:
        self.item = self._get_item()
        self.ctb = self._get_ctb()
        self._update_bribe_gil_spent()
        if self.item is not None:
            self.monster.statuses[Status.EJECT] = 254

    def __str__(self) -> str:
        string = f'{self.character} -> Bribe [{self.ctb}]: {self.monster} -> '
        if self.item is not None:
            string += f'{self.item}'
        else:
            string += 'Fail'
        string += f' | Total Gil spent: {self.bribe_gil_spent}'
        return string

    def _get_item(self) -> ItemDrop | None:
        # TODO
        # should this happen here or after some rng rolls?
        if self.monster.monster.bribe.item is None:
            return

        chance_rng_index = min(60 + self.monster.index, 67)
        chance_rng = self._advance_rng(chance_rng_index)

        if (Configs.game_version in (GameVersion.HD, GameVersion.PS2INT)
                and self.gil < 1):
            return

        if (self.monster.monster.immune_to_bribe
                or Status.SLEEP in self.monster.statuses):
            return

        gil = self.gil + self.monster.bribe_gil_spent
        chance = int(gil * 256 / self.monster.monster.stats[Stat.HP] / 20) - 64
        if (chance_rng & 255) >= chance:
            return

        rng_index = min(20 + self.character.index, 27)
        variance_rng = self._advance_rng(rng_index)
        rounding_rng = self._advance_rng(rng_index)
        quantity = int(sqrt(chance)
                       * self.monster.monster.bribe.item.quantity
                       * 0.0625
                       * ((variance_rng % 11) + 20)
                       / 25
                       + (rounding_rng & 1)
                       )
        drop = ItemDrop(
            item=self.monster.monster.bribe.item.item,
            quantity=min(max(1, quantity), 99),
            rare=False,
            )
        return drop

    def _update_bribe_gil_spent(self) -> None:
        if self.gil >= 1:
            self.monster.bribe_gil_spent += self.gil
        self.bribe_gil_spent = self.monster.bribe_gil_spent

    def _get_ctb(self) -> int:
        ctb = self.character.base_ctb * 3
        if Status.HASTE in self.character.statuses:
            ctb = ctb // 2
        elif Status.SLOW in self.character.statuses:
            ctb = ctb * 2
        self.character.ctb += ctb
        return ctb
