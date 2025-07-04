from collections.abc import Iterator

from .data.constants import RNG_CONSTANTS_1, RNG_CONSTANTS_2


class FFXRNGTracker:
    """Used to calculate, cache and track values generated
    by the RNG function in FFX. From a seed is produced an
    array of 68 values and those are used as the argument
    of the RNG function to generate a new value, that
    replaces the old one. Each value in the array is used
    in one or a handful of cases:
        0: encounter chance
        1: encounter formations and preemptive/ambush
        2: monster ai and animations
        4: monster targeting
        5: multihit actions targeting
        9: screenshake
        10: drop/steal chance
        11: rare item chance
        12: equipment owner, type, number of slots/abilities
        13: abilities
        14: camera
        17: yojimbo motivation
        20-35: damage/crit/escape chance
        36-51: hit chance
        52-67: status landing chance
    """

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng_initial_values = self.get_rng_initial_values()

        # get rng generators
        self._rng_generators = tuple(
            [self.get_rng_generator(i) for i in range(68)])
        # create a list of lists used to store rng values
        self._rng_arrays = [list() for _ in range(68)]
        self.rng_current_positions = [0 for _ in range(68)]

    def __repr__(self) -> str:
        return f'{type(self).__name__}(seed=({self.seed}))'

    def get_rng_initial_values(self, amount: int = 68) -> list[int]:
        """Calculates the starting values of the rng arrays."""
        rng_value = ((self.seed & 0xffffffff) ^ 0x80000000) - 0x80000000
        initial_values = []
        for _ in range(amount):
            rng_value = rng_value * 0x5d588b65 + 0x3c35
            rng_value = ((rng_value & 0xffffffff) ^ 0x80000000) - 0x80000000
            rng_value = (rng_value >> 0x10) + (rng_value << 0x10)
            rng_value = ((rng_value & 0xffffffff) ^ 0x80000000) - 0x80000000
            initial_values.append(rng_value & 0x7fffffff)
        return initial_values

    def get_rng_generator(self, rng_index: int) -> Iterator[int]:
        """Returns a generator object that yields rng values
        for a given rng index.
        """
        rng_value = self.rng_initial_values[rng_index]
        rng_value = ((rng_value & 0xffffffff) ^ 0x80000000) - 0x80000000
        rng_constant_1 = RNG_CONSTANTS_1[rng_index]
        rng_constant_2 = RNG_CONSTANTS_2[rng_index]

        while True:
            rng_value = rng_value * rng_constant_1 ^ rng_constant_2
            rng_value = ((rng_value & 0xffffffff) ^ 0x80000000) - 0x80000000
            rng_value = (rng_value >> 0x10) + (rng_value << 0x10)
            rng_value = ((rng_value & 0xffffffff) ^ 0x80000000) - 0x80000000
            yield rng_value & 0x7fffffff

    def advance_rng(self, index: int) -> int:
        """Advances the position of the given rng index and returns
        the next value for that index.
        """
        array = self._rng_arrays[index]
        position = self.rng_current_positions[index]
        self.rng_current_positions[index] = position + 1
        try:
            rng_value = array[position]
        except IndexError:
            rng_value = next(self._rng_generators[index])
            array.append(rng_value)
        return rng_value

    def reset(self) -> None:
        """Reset the position of the rng arrays."""
        self.rng_current_positions.clear()
        self.rng_current_positions.extend(0 for _ in range(68))
