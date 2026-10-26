"""
What the player knows about the world.

Primitives and skills must never use more information than the player can
see or has seen. The player sees a window of OBS_DIM cells centred on itself,
and inside it only lit cells (light_map > 0.05), exactly like the game's own
renderer. Every cell it has seen is remembered per floor, with the value it
had when it was last seen.

All world information must be read through the functions of this module:
    known_blocks, known_items   remembered map of the current floor
    visible_mask, is_visible    what is in view right now
    visible_mobs                mobs in view (class, type id, position, health)
    visible_player_projectiles  the player's own projectiles in view
    ladder_open                 whether the down ladder of this floor is open
    boss_vulnerable             whether the necromancer can be hit right now
"""

import numpy as np

# Value of never-seen cells in known_blocks / known_items
UNKNOWN = -1

LIGHT_THRESHOLD = 0.05


class Knowledge:
    """
    Per-floor memory of every block and item the player has seen.

    The agent loop resets it when a new world starts and saves it with the
    world checkpoint. Reading through known_blocks / known_items observes the
    given state first, so the memory is always up to date.
    """

    def __init__(self):
        self.blocks = None
        self.items = None
        self.last_timestep = -1

    def reset(self):
        self.blocks = None
        self.items = None
        self.last_timestep = -1

    def observe(self, state):
        map_shape = tuple(state.map.shape)

        if self.blocks is None or self.blocks.shape != map_shape:
            self.blocks = np.full(map_shape, UNKNOWN, dtype=np.int32)
            self.items = np.full(map_shape, UNKNOWN, dtype=np.int32)

        # An outdated state (e.g. a skill passing an old state variable) must
        # not overwrite newer memory
        timestep = int(state.timestep)
        if timestep < self.last_timestep:
            return
        self.last_timestep = timestep

        level = int(state.player_level)
        mask = visible_mask(state)

        self.blocks[level][mask] = np.asarray(state.map[level])[mask]
        self.items[level][mask] = np.asarray(state.item_map[level])[mask]

    def state_dict(self):
        return {
            "blocks": None if self.blocks is None else self.blocks.copy(),
            "items": None if self.items is None else self.items.copy(),
            "last_timestep": self.last_timestep,
        }

    def load_state_dict(self, state_dict):
        self.blocks = state_dict["blocks"]
        self.items = state_dict["items"]
        self.last_timestep = state_dict["last_timestep"]


knowledge = Knowledge()


def visible_mask(state):
    """
    Cells of the current floor the player can see right now.

    Args:
        state: Current EnvState

    Returns:
        Boolean array (map rows, map cols): True inside the view window around
        the player where the cell is lit
    """
    from craftax.craftax.constants import OBS_DIM

    level = int(state.player_level)
    map_rows, map_cols = state.map.shape[1:]
    player_row = int(state.player_position[0])
    player_col = int(state.player_position[1])

    row_start = max(0, player_row - OBS_DIM[0] // 2)
    row_end = min(map_rows, player_row + OBS_DIM[0] // 2 + 1)
    col_start = max(0, player_col - OBS_DIM[1] // 2)
    col_end = min(map_cols, player_col + OBS_DIM[1] // 2 + 1)

    mask = np.zeros((map_rows, map_cols), dtype=bool)
    mask[row_start:row_end, col_start:col_end] = (
        np.asarray(state.light_map[level, row_start:row_end, col_start:col_end])
        > LIGHT_THRESHOLD
    )
    return mask


def is_visible(state, row, col):
    """
    Whether the cell (row, col) of the current floor is in view and lit.

    Args:
        state: Current EnvState
        row, col: Map coordinates

    Returns:
        True if the player can see the cell right now
    """
    map_rows, map_cols = state.map.shape[1:]
    if not (0 <= row < map_rows and 0 <= col < map_cols):
        return False
    return bool(visible_mask(state)[row, col])


def known_blocks(state):
    """
    The player's memory of the blocks on the current floor.

    Args:
        state: Current EnvState

    Returns:
        Int array (map rows, map cols) of BlockType values as last seen,
        UNKNOWN (-1) for cells never seen
    """
    knowledge.observe(state)
    return knowledge.blocks[int(state.player_level)].copy()


def known_items(state):
    """
    The player's memory of the items (torches, ladders) on the current floor.

    Args:
        state: Current EnvState

    Returns:
        Int array (map rows, map cols) of ItemType values as last seen,
        UNKNOWN (-1) for cells never seen
    """
    knowledge.observe(state)
    return knowledge.items[int(state.player_level)].copy()


def visible_mobs(state):
    """
    Mobs the player can see right now.

    Args:
        state: Current EnvState

    Returns:
        List of (MobType, type_id, row, col, health) for every living
        passive, melee and ranged mob in view on the current floor
    """
    from craftax.craftax.constants import MobType

    level = int(state.player_level)
    mask = visible_mask(state)
    mobs = []

    for mob_class, mob_array in (
        (MobType.PASSIVE, state.passive_mobs),
        (MobType.MELEE, state.melee_mobs),
        (MobType.RANGED, state.ranged_mobs),
    ):
        alive = np.asarray(mob_array.mask[level])
        positions = np.asarray(mob_array.position[level])
        type_ids = np.asarray(mob_array.type_id[level])
        healths = np.asarray(mob_array.health[level])

        for index in range(len(alive)):
            if not alive[index]:
                continue
            row, col = int(positions[index][0]), int(positions[index][1])
            if 0 <= row < mask.shape[0] and 0 <= col < mask.shape[1] and mask[row, col]:
                mobs.append(
                    (mob_class, int(type_ids[index]), row, col, float(healths[index]))
                )

    return mobs


def visible_player_projectiles(state):
    """
    The player's own projectiles (arrows, fireballs, iceballs) in view.

    Args:
        state: Current EnvState

    Returns:
        List of (type_id, row, col) for every player projectile in view
    """
    level = int(state.player_level)
    mask = visible_mask(state)
    projectiles = state.player_projectiles

    alive = np.asarray(projectiles.mask[level])
    positions = np.asarray(projectiles.position[level])
    type_ids = np.asarray(projectiles.type_id[level])

    result = []
    for index in range(len(alive)):
        if not alive[index]:
            continue
        row, col = int(positions[index][0]), int(positions[index][1])
        if 0 <= row < mask.shape[0] and 0 <= col < mask.shape[1] and mask[row, col]:
            result.append((int(type_ids[index]), row, col))

    return result


def ladder_open(state):
    """
    Whether the down ladder of the current floor is open (shown as "Ladder Open").

    Args:
        state: Current EnvState

    Returns:
        True once enough monsters were killed on this floor
    """
    from craftax.craftax.constants import MONSTERS_KILLED_TO_CLEAR_LEVEL

    level = int(state.player_level)
    return int(state.monsters_killed[level]) >= MONSTERS_KILLED_TO_CLEAR_LEVEL


def boss_vulnerable(state):
    """
    Whether the necromancer can be hit right now (shown as "Is Boss Vulnerable").

    Args:
        state: Current EnvState

    Returns:
        True if the necromancer is vulnerable
    """
    from craftax.craftax.util.game_logic_utils import is_boss_vulnerable

    return bool(is_boss_vulnerable(state))
