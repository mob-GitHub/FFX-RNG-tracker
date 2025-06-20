from abc import ABC, abstractmethod
from typing import Callable, Generator, Protocol

from .actions import ACTIONS, COMMAND_BIN, Action
from .actor import Actor, CharacterActor, MonsterActor
from .constants import Status, TargetType

type ActionGenerator = Generator[tuple[Action, list[Actor]]]


class MagusCommand(Protocol):
    def __call__(self, one_more_time: bool = False) -> ActionGenerator:
        ...


class MagusSister(ABC):
    actor: CharacterActor

    def __init__(self,
                 cindy: CharacterActor,
                 sandy: CharacterActor,
                 mindy: CharacterActor,
                 advance_rng: Callable[[int], int],
                 monster_party: list[MonsterActor],
                 ) -> None:
        self.cindy = cindy
        self.sandy = sandy
        self.mindy = mindy
        self.advance_rng = advance_rng
        self.monster_party = monster_party
        self.reset()

    def reset(self) -> None:
        self.action_to_repeat: Action | None = None
        self.magus_last_command_id: int | None = None
        self._motivation = 50
        self._pending_motivation_2 = 0
        self._pending_motivation = 0
        self._pending_od_2 = 0
        self._pending_od = 0
        self._field_0x715 = 0

    @property
    def motivation(self) -> int:
        return self._motivation

    @motivation.setter
    def motivation(self, value: int) -> None:
        self._motivation = min(max(0, value), 100)

    def _set_pending_motivation_and_overdrive(self,
                                              pending_od: int,
                                              pending_motivation: int,
                                              ) -> None:
        if self.action_to_repeat is not None:
            return
        self._set_pending_motivation_and_overdrive_2(
            pending_od=pending_od,
            pending_motivation=pending_motivation,
            pending_od_2=pending_od,
            pending_motivation_2=pending_motivation,
            )

    def _set_pending_motivation_and_overdrive_2(self,
                                                pending_od: int,
                                                pending_motivation: int,
                                                pending_od_2: int,
                                                pending_motivation_2: int,
                                                ) -> None:
        self._pending_motivation_2 = pending_motivation_2
        self._pending_motivation = pending_motivation
        self._pending_od_2 = pending_od_2
        self._pending_od = pending_od

    def set_field_0x715(self,
                        last_action: Action,
                        hp_damage: int,
                        mp_damage: int,
                        ctb_damage: int,
                        ) -> None:
        if last_action.name == 'Taking a break...':
            self._field_0x715 = 0
        elif (not last_action.damages_hp
                and not last_action.damages_mp
                and not last_action.damages_ctb):
            self._field_0x715 = 1
        elif last_action.name == 'Haste':
            self._field_0x715 = 1
        elif last_action.heals:
            if hp_damage >= 0 and mp_damage >= 0 and ctb_damage >= 0:
                self._field_0x715 = 0
            else:
                self._field_0x715 = 1
        else:  # is damaging
            if hp_damage <= 0 and mp_damage <= 0 and ctb_damage <= 0:
                self._field_0x715 = 0
            else:
                self._field_0x715 = 1

    def resolve_pending_motivation_and_overdrive(self) -> None:
        if self._field_0x715 == 1:
            self.motivation += self._pending_motivation
            self.actor.current_od += self._pending_od
        else:
            self.motivation += self._pending_motivation_2
            self.actor.current_od += self._pending_od_2

    def _roll_magus_random(self,
                           action: Action | None,
                           chance: int | None,
                           ) -> bool:
        if chance is None:
            return True
        if action is None or self.action_to_repeat is None:
            chance = min(max(0, chance), 255)
            return self.advance_rng(18) & 255 < chance
        return action == self.action_to_repeat

    def _btl_get_command_target_search(self,
                                       action: Action,
                                       targeting: TargetType,
                                       chance: int | None,
                                       ) -> list[Actor] | None:
        possible_targets: list[Actor] = []
        if targeting in (TargetType.CINDY, TargetType.CINDY_NOT_REFLECT):
            if (Status.DEATH in self.cindy.statuses
                    and not action.can_target_dead):
                return
            if Status.EJECT in self.cindy.statuses:
                return
            possible_targets.append(self.cindy)
        elif targeting in (TargetType.RANDOM_MONSTER, TargetType.MONSTERS_PARTY):
            for monster in self.monster_party:
                if (Status.DEATH in monster.statuses
                        and not action.can_target_dead):
                    continue
                possible_targets.append(monster)
        else:
            for actor in (self.cindy, self.sandy, self.mindy):
                if (Status.DEATH in actor.statuses
                        and not action.can_target_dead):
                    continue
                if Status.EJECT in actor.statuses:
                    continue
                possible_targets.append(actor)
            if targeting is TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED:
                if self.actor in possible_targets:
                    possible_targets.remove(self.actor)
        if not possible_targets:
            return

        if (action.od_cost > 0
                and ((self.actor.max_od > self.actor.current_od)
                     or Status.CURSE in self.actor.statuses)):
            return

        if (action.affected_by_silence
                and Status.SILENCE in self.actor.statuses):
            return

        if action.mp_cost > self.actor.current_mp:
            return

        if not self._roll_magus_random(action, chance):
            return

        match targeting:
            # the script never actually uses these targeting options
            # but effectively uses whatever was found in the previous
            # part of the function as the targets without any further filtering
            case TargetType.MONSTERS_PARTY | TargetType.PARTY:
                if len(possible_targets) > 1:
                    self.advance_rng(4)
                return possible_targets * max(1, action.n_of_hits)
            # just as above but the targets are filtered before advancing rng4
            # then the targets without filtering are used
            case TargetType.PARTY_NOT_NULALL:
                # TODO
                # doublecheck this
                target_check = [c for c in possible_targets
                                if Status.NULTIDE not in c.statuses
                                or Status.NULBLAZE not in c.statuses
                                or Status.NULSHOCK not in c.statuses
                                or Status.NULFROST not in c.statuses]
                if not target_check:
                    return
                if len(target_check) > 1:
                    self.advance_rng(4)
                return possible_targets * max(1, action.n_of_hits)
            case TargetType.RANDOM_MONSTER | TargetType.RANDOM_CHARACTER:
                pass
            case TargetType.RANDOM_CHARACTER_NOT_AUTOLIFE:
                possible_targets = [c for c in possible_targets
                                    if Status.AUTOLIFE not in c.statuses]
            case TargetType.RANDOM_CHARACTER_DEATH:
                possible_targets = [c for c in possible_targets
                                    if Status.DEATH in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_SHELL_NOT_REFLECT:
                possible_targets = [c for c in possible_targets
                                    if Status.SHELL not in c.statuses
                                    and Status.REFLECT not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_PROTECT_NOT_REFLECT:
                possible_targets = [c for c in possible_targets
                                    if Status.PROTECT not in c.statuses
                                    and Status.REFLECT not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_HASTE_NOT_REFLECT:
                possible_targets = [c for c in possible_targets
                                    if Status.HASTE not in c.statuses
                                    and Status.REFLECT not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED:
                # the user is already removed in the previous part
                # of the function
                possible_targets = [c for c in possible_targets
                                    if c.current_hp < c.max_hp]
            case TargetType.CINDY_NOT_REFLECT:
                possible_targets = [c for c in possible_targets
                                    if Status.REFLECT not in c.statuses]
            case TargetType.CINDY:
                pass
            case _:
                raise Exception(targeting)

        if not possible_targets:
            return

        if len(possible_targets) == 1:
            return possible_targets * max(1, action.n_of_hits)
        target_rng = self.advance_rng(4)
        target_index = target_rng % len(possible_targets)
        return [possible_targets[target_index]] * max(1, action.n_of_hits)

    @abstractmethod
    def get_command_list(self) -> dict[str, MagusCommand]:
        commands: dict[str, MagusCommand] = {}
        chars = self.cindy, self.mindy, self.sandy
        if len(tuple(c for c in chars if c.current_od >= c.max_od)) == 3:
            commands['Combine powers!'] = self.combine_powers
        # TODO
        # od is not properly increased outside of using commands
        # this command is always active for now
        else:
            commands['Combine powers!'] = self.combine_powers
        commands['Dismiss'] = self.dismiss
        # not an actual command, added here for convenience
        commands['Auto-Life'] = self.autolife
        return commands

    def combine_powers(self, one_more_time: bool = False) -> ActionGenerator:
        self.action_to_repeat = None
        # Delta Attack
        result = self._attempt_move(
            0xea, TargetType.MONSTERS_PARTY, self.motivation + 200, 0, 10)
        if result is not None:
            yield result
            return
        yield self._taking_a_break(-10)

    def dismiss(self, one_more_time: bool = False) -> ActionGenerator:
        yield COMMAND_BIN[0x56], [self.actor]

    def on_summon(self) -> None:
        return

    def on_dismiss(self) -> None:
        if Status.DEATH in self.actor.statuses:
            self.actor.statuses.pop(Status.DEATH)
            self.actor.current_hp = 1
        self.actor.ctb = self.actor.base_ctb * 3
        self.magus_last_command_id = None

    def autolife(self, one_more_time: bool = False) -> ActionGenerator:
        # TODO
        # check if resolve_pending_motivation_and_overdrive is called
        # when autolife procs
        # if it doesnt remove this and just use autolife as an action
        yield ACTIONS['auto-life_counter'], [self.actor]

    def _taking_a_break(self,
                        motivation: int = -5,
                        ) -> tuple[Action, list[Actor]]:
        self._set_pending_motivation_and_overdrive(0, motivation)
        return ACTIONS['taking_a_break...'], [self.actor]

    def _attempt_move(self,
                      action_id: int,
                      targeting: TargetType,
                      chance: int | None,
                      od: int,
                      motivation: int,
                      ) -> tuple[Action, list[Actor]] | None:
        action = COMMAND_BIN[action_id]
        # this check actually happens inside _btl_get_command_target_search
        # but there is no sideffects between here and there
        # so we can decide now
        if (chance is not None and self.action_to_repeat is not None
                and action != self.action_to_repeat):
            return
        target = self._btl_get_command_target_search(action, targeting, chance)
        if target is not None:
            self._set_pending_motivation_and_overdrive(od, motivation)
            return action, target

    def _attempt_moves(self,
                       actions: tuple[tuple[int, TargetType, int | None, int, int], ...],
                       ) -> tuple[Action, list[Actor]] | None:
        for action_info in actions:
            if (result := self._attempt_move(*action_info)) is not None:
                return result


class Cindy(MagusSister):
    def __init__(self,
                 cindy: CharacterActor,
                 sandy: CharacterActor,
                 mindy: CharacterActor,
                 advance_rng: Callable[[int], int],
                 monster_party: list[MonsterActor],
                 ) -> None:
        self.actor = cindy
        super().__init__(cindy, sandy, mindy, advance_rng, monster_party)

    def on_summon(self) -> None:
        super().on_summon()
        self.resolve_pending_motivation_and_overdrive()

    def on_dismiss(self) -> None:
        super().on_dismiss()
        self.resolve_pending_motivation_and_overdrive()
        self.actor.ctb = 0

    def get_command_list(self) -> dict[str, MagusCommand]:
        commands: dict[str, MagusCommand] = {}
        commands['Do as you will.'] = self.do_as_you_will
        if self.magus_last_command_id is not None:
            commands['One more time.'] = self.one_more_time
        if self._roll_magus_random(None, self.motivation + 50):
            commands['Fight!'] = self.fight
        if self._roll_magus_random(None, 128):
            commands['Go, go!'] = self.go_go
        if self._roll_magus_random(None, 200):
            commands['Help each other!'] = self.help_each_other
        commands.update(super().get_command_list())
        return commands

    def one_more_time(self, one_more_time: bool = False) -> ActionGenerator:
        m = self.motivation
        if self._roll_magus_random(None, m + 150):
            self._set_pending_motivation_and_overdrive_2(2, 4, 0, -6)
            self.action_to_repeat = self.actor.last_action
            match self.magus_last_command_id:
                case 1:
                    pass
                case 2:
                    yield from self.fight(one_more_time=True)
                    return
                case 3:
                    yield from self.go_go(one_more_time=True)
                    return
                case 4:
                    yield from self.help_each_other(one_more_time=True)
                    return
                case _:
                    yield from self.do_as_you_will(one_more_time=True)
                    return
        else:
            self.action_to_repeat = None
            self.magus_last_command_id = 1
        result = self._attempt_moves((
            (0xe5, TargetType.RANDOM_MONSTER, m, 1, 2),  # Camisade
            (0, TargetType.RANDOM_MONSTER, None, 1, 2),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def do_as_you_will(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 0
        m = self.motivation
        result = self._attempt_moves((
            (0x40, TargetType.RANDOM_CHARACTER_NOT_AUTOLIFE, m + 50, 3, 10),  # Auto-Life # noqa:E501
            (0x35, TargetType.RANDOM_CHARACTER_DEATH, (m + 50) // 2, 2, 6),  # Full-Life # noqa:E501
            (0x34, TargetType.RANDOM_CHARACTER_DEATH, (m + 200) // 2, 1, 5),  # Life # noqa:E501
            (0, TargetType.RANDOM_MONSTER, m, 1, 2),  # Attack
            (0x52, TargetType.RANDOM_MONSTER, m // 8, 2, 6),  # Flare
        ))
        if result is not None:
            yield result
            return
        if (self._roll_magus_random(None, 128)
                or self.action_to_repeat is not None):
            result = self._attempt_moves((
                (0x49, TargetType.RANDOM_MONSTER, m // 2, 1, 2),  # Firaga
                (0x4b, TargetType.RANDOM_MONSTER, m // 2, 1, 2),  # Thundaga
                (0x4a, TargetType.RANDOM_MONSTER, m // 2, 1, 2),  # Blizzaga
                (0x4c, TargetType.RANDOM_MONSTER, m // 2, 1, 2),  # Waterga
            ))
            if result is not None:
                yield result
                return
        yield self._taking_a_break()

    def fight(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 2
        m = self.motivation
        result = self._attempt_moves((
            (0xe5, TargetType.RANDOM_MONSTER, m + 20, 2, 4),  # Camisade
            (0, TargetType.RANDOM_MONSTER, m + 150, 1, 3),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def go_go(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 3
        current_hp = self.actor.current_hp
        max_hp = self.actor.max_hp
        if current_hp < max_hp or self.action_to_repeat is not None:
            # Pray
            result = self._attempt_move(
                0x19, TargetType.PARTY,
                (max_hp - current_hp) * 256 // max_hp, 1, 1)
            if result is not None:
                yield result
                return
        current_mp = self.actor.current_mp
        max_mp = self.actor.max_mp
        if current_mp < max_mp or self.action_to_repeat is not None:
            # Osmose
            result = self._attempt_move(
                0x51, TargetType.RANDOM_MONSTER,
                (max_mp - current_mp) * 256 // max_mp, 1, 1)
            if result is not None:
                yield result
                return
        m = self.motivation
        # Attack
        result = self._attempt_move(0, TargetType.RANDOM_MONSTER, m * 2, 1, 2)
        if result is not None:
            yield result
            return
        if (self._roll_magus_random(None, m // 2)
                or self.action_to_repeat is not None):
            result = self._attempt_moves((
                (0x53, TargetType.MONSTERS_PARTY, max(m - 80, 0), 5, 10),  # Ultima # noqa:E501
                (0x52, TargetType.RANDOM_MONSTER, m // 8, 2, 6),  # Flare
                (0x50, TargetType.RANDOM_MONSTER, m // 2, 2, 6),  # Drain
                (0x4A, TargetType.RANDOM_MONSTER, m, 1, 2),  # Blizzaga
                (0x4C, TargetType.RANDOM_MONSTER, m, 1, 2),  # Waterga
                (0x4B, TargetType.RANDOM_MONSTER, m, 1, 2),  # Thundaga
                (0x49, TargetType.RANDOM_MONSTER, m, 1, 2),  # Firaga
                (0, TargetType.RANDOM_MONSTER, None, 1, 2),  # Attack
            ))
            if result is not None:
                yield result
                return
        # Camisade
        result = self._attempt_move(0xe5, TargetType.RANDOM_MONSTER, m, 3, 5)
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def help_each_other(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 4
        m = self.motivation
        result = self._attempt_moves((
            (0x35, TargetType.RANDOM_CHARACTER_DEATH, m, 1, 2),  # Full-Life
            (0x34, TargetType.RANDOM_CHARACTER_DEATH, m + 150, 1, 1),  # Life
            (0x40, TargetType.RANDOM_CHARACTER_NOT_AUTOLIFE, m + 50, 3, 10),  # Auto-Life # noqa:E501
            (0x2B, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 2, 1, 2),  # Cure # noqa:E501
            (0x2C, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 2, 1, 2),  # Cura # noqa:E501
            (0x2D, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 2, 1, 2),  # Curaga # noqa:E501
            (0xe5, TargetType.RANDOM_MONSTER, m, 3, 5),  # Camisade
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()


class Sandy(MagusSister):
    def __init__(self,
                 cindy: CharacterActor,
                 sandy: CharacterActor,
                 mindy: CharacterActor,
                 advance_rng: Callable[[int], int],
                 monster_party: list[MonsterActor],
                 ) -> None:
        self.actor = sandy
        super().__init__(cindy, sandy, mindy, advance_rng, monster_party)

    def get_command_list(self) -> dict[str, MagusCommand]:
        commands: dict[str, MagusCommand] = {}
        commands['Do as you will.'] = self.do_as_you_will
        if self.magus_last_command_id is not None:
            commands['One more time.'] = self.one_more_time
        if self._roll_magus_random(None, self.motivation + 150):
            commands['Fight!'] = self.fight
        chars = self.cindy, self.sandy, self.mindy
        # TODO
        # condition might not be accurate
        # Check (FrontlineChars.NearDeath or Battle.RollMagusRandom(unknown=0, chance=128))
        if (self._roll_magus_random(None, 128)
                or any(c.current_hp < (c.max_hp / 4) for c in chars)):
            commands['Defense!'] = self.defense
        commands.update(super().get_command_list())
        return commands

    def one_more_time(self, one_more_time: bool = False) -> ActionGenerator:
        if self._roll_magus_random(None, self.motivation + 120):
            self._set_pending_motivation_and_overdrive_2(2, 4, 0, -6)
            self.action_to_repeat = self.actor.last_action
            match self.magus_last_command_id:
                case 1:
                    pass
                case 2:
                    yield from self.fight(one_more_time=True)
                    return
                case 5:
                    yield from self.defense(one_more_time=True)
                    return
                case _:
                    yield from self.do_as_you_will(one_more_time=True)
                    return
        else:
            self.action_to_repeat = None
            self.magus_last_command_id = 1
        result = self._attempt_moves((
            (0xe7, TargetType.RANDOM_MONSTER, 128, 1, 2),  # Razzia
            (0, TargetType.RANDOM_MONSTER, None, 1, 2),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def do_as_you_will(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 0
        m = self.motivation
        result = self._attempt_moves((
            (0x3C, TargetType.CINDY_NOT_REFLECT, m + 200, 2, 2),  # Reflect
            (0xe7, TargetType.RANDOM_MONSTER, 128, 1, 2),  # Razzia
            (0, TargetType.RANDOM_MONSTER, None, 1, 2),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def fight(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 2
        m = self.motivation
        result = self._attempt_moves((
            (0xe7, TargetType.RANDOM_MONSTER, m + 50, 2, 4),  # Razzia
            (0, TargetType.RANDOM_MONSTER, m + 180, 1, 3),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def defense(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.action_to_repeat = None
            self.magus_last_command_id = 5
        m = self.motivation
        result = self._attempt_moves((
            (0x3a, TargetType.RANDOM_CHARACTER_NOT_SHELL_NOT_REFLECT, m + 50, 1, 2),  # Shell # noqa:E501
            (0x3b, TargetType.RANDOM_CHARACTER_NOT_PROTECT_NOT_REFLECT, m + 50, 1, 2),  # Protect # noqa:E501
            (0x36, TargetType.RANDOM_CHARACTER_NOT_HASTE_NOT_REFLECT, m, 1, 2),  # Haste # noqa:E501
            (0x12d, TargetType.PARTY_NOT_NULALL, m + 50, 1, 2),  # NulAll
            (0x2b, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 4, 1, 2),  # Cure # noqa:E501
            (0x2c, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 6, 1, 2),  # Cura # noqa:E501
            (0x2d, TargetType.RANDOM_CHARACTER_NOT_USER_DAMAGED, m // 8, 1, 2),  # Curaga # noqa:E501
            (0xe7, TargetType.RANDOM_MONSTER, m, 2, 2),  # Razzia
            (0, TargetType.RANDOM_MONSTER, m, 1, 2),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()


class Mindy(MagusSister):
    def __init__(self,
                 cindy: CharacterActor,
                 sandy: CharacterActor,
                 mindy: CharacterActor,
                 advance_rng: Callable[[int], int],
                 monster_party: list[MonsterActor],
                 ) -> None:
        self.actor = mindy
        self.last_do_as_you_will_actions: list[int] = []
        super().__init__(cindy, sandy, mindy, advance_rng, monster_party)

    def reset(self) -> None:
        super().reset()
        self.last_do_as_you_will_actions.clear()

    def get_command_list(self) -> dict[str, MagusCommand]:
        commands: dict[str, MagusCommand] = {}
        commands['Do as you will.'] = self.do_as_you_will
        if self.magus_last_command_id is not None:
            commands['One more time.'] = self.one_more_time
        if self._roll_magus_random(None, self.motivation + 150):
            commands['Fight!'] = self.fight
        current_hp = self.actor.current_hp
        max_hp = self.actor.max_hp
        current_mp = self.actor.current_mp
        max_mp = self.actor.max_mp
        if current_hp * 4 // max_hp == 0 or current_mp * 4 // max_mp == 0:
            if self._roll_magus_random(None, 200):
                commands['Are you all right?'] = self.are_you_all_right
        elif current_hp * 2 // max_hp == 0 or current_mp * 2 // max_mp == 0:
            if self._roll_magus_random(None, 128):
                commands['Are you all right?'] = self.are_you_all_right
        commands.update(super().get_command_list())
        return commands

    def one_more_time(self, one_more_time: bool = False) -> ActionGenerator:
        m = self.motivation
        if self._roll_magus_random(None, m + 120):
            self._set_pending_motivation_and_overdrive_2(2, 4, 0, -15)
            self.action_to_repeat = self.actor.last_action
            match self.magus_last_command_id:
                case 1:
                    pass
                case 2:
                    yield from self.fight(one_more_time=True)
                    return
                case 6:
                    yield from self.are_you_all_right(one_more_time=True)
                    return
                case _:
                    yield from self.do_as_you_will(one_more_time=True)
                    return
        else:
            self.last_do_as_you_will_actions.clear()
            self.action_to_repeat = None
            self.magus_last_command_id = 1
        result = self._attempt_moves((
            (0xe9, TargetType.RANDOM_MONSTER, 128, 1, 2),  # Passado
            (0, TargetType.RANDOM_MONSTER, m + 100, 1, 3),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def do_as_you_will(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.last_do_as_you_will_actions.clear()
            self.action_to_repeat = None
            self.magus_last_command_id = 0
        if self.cindy.current_hp > 0:
            if self.last_do_as_you_will_actions:
                for action_id in self.last_do_as_you_will_actions:
                    result = self._attempt_move(
                        action_id, TargetType.CINDY, None, 0, 0)
                    if result is not None:
                        yield result
                return
            if (Status.REFLECT in self.cindy.statuses
                    and self.action_to_repeat is None):
                if self._roll_magus_random(None, self.motivation):
                    actions_to_use = 2
                else:
                    actions_to_use = 1
                for _ in range(actions_to_use):
                    m = self.motivation
                    actions_list = (
                        (0x52, TargetType.CINDY, m // 2, 2, 3),  # Flare
                        (0x4d, TargetType.CINDY, m // 2, 2, 2),  # Bio
                        (0x4f, TargetType.CINDY, m // 2, 2, 2),  # Death
                        (0x49, TargetType.CINDY, m, 1, 2),  # Firaga
                        (0x4B, TargetType.CINDY, m, 1, 2),  # Thundaga
                        (0x4C, TargetType.CINDY, m, 1, 2),  # Waterga
                        (0x4A, TargetType.CINDY, m, 1, 2),  # Blizzaga
                        (0x45, TargetType.CINDY, m, 1, 2),  # Fira
                        (0x47, TargetType.CINDY, m, 1, 2),  # Thundara
                        (0x48, TargetType.CINDY, m, 1, 2),  # Watera
                        (0x46, TargetType.CINDY, m, 1, 2),  # Blizzara
                        (0x50, TargetType.CINDY, m, 0, 1),  # Drain
                    )
                    for action_info in actions_list:
                        result = self._attempt_move(*action_info)
                        if result is not None:
                            self.last_do_as_you_will_actions.append(
                                action_info[0])
                            yield result
                            break
                if self.last_do_as_you_will_actions:
                    return
        m = self.motivation
        result = self._attempt_moves((
            (0xe9, TargetType.RANDOM_MONSTER, m + 100, 1, 3),  # Passado
            (0, TargetType.RANDOM_MONSTER, m + 100, 1, 3),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def fight(self, one_more_time: bool = False) -> ActionGenerator:
        if not one_more_time:
            self.last_do_as_you_will_actions.clear()
            self.action_to_repeat = None
            self.magus_last_command_id = 2
        m = self.motivation
        result = self._attempt_moves((
            (0xe9, TargetType.RANDOM_MONSTER, m + 30, 2, 4),  # Passado
            (0, TargetType.RANDOM_MONSTER, m + 180, 1, 3),  # Attack
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break()

    def are_you_all_right(self,
                          one_more_time: bool = False,
                          ) -> ActionGenerator:
        if not one_more_time:
            self.last_do_as_you_will_actions.clear()
            self.action_to_repeat = None
            self.magus_last_command_id = 6
        m = self.motivation
        hp_chance = (((self.actor.max_hp - self.actor.current_hp) * 256)
                     // (self.actor.max_hp * 2))
        mp_chance = (((self.actor.max_mp - self.actor.current_mp) * 256)
                     // (self.actor.max_mp * 2))
        result = self._attempt_moves((
            (0x20, TargetType.RANDOM_MONSTER, m // 2, 2, 3),  # Lancet
            (0x50, TargetType.RANDOM_MONSTER, hp_chance, 2, 3),  # Drain
            (0x51, TargetType.RANDOM_MONSTER, mp_chance, 2, 3),  # Osmose
        ))
        if result is not None:
            yield result
            return
        yield self._taking_a_break(-1)
