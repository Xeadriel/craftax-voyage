# Skill: place_furnace
# Purpose: Places a furnace
# Required inputs: target_position (tuple), max_steps (int)
# Preconditions: Player must be near the target position, have 1 stone in inventory
# Expected effects: Furnace is placed at target position, inventory updated
# Failure conditions: Invalid position, no stone in inventory, solid block at target
# Explanation: Uses state.map for block placement validation, state.inventory for stone availability,
#             Action.PLACE_FURNACE for furnace placement

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import in_bounds, is_in_solid_block


def place_furnace(
    state: EnvState, target_position: tuple, max_steps: int = 100
) -> bool:
    """
    Places a furnace.

    Returns True if furnace was placed, False otherwise.
    """
    # Check if we have 1 stone in inventory
    if state.inventory.stone <= 0:
        return False

    # Check if target position is in bounds
    if not in_bounds(state, target_position):
        return False

    # Check if target position is a solid block
    if is_in_solid_block(state, target_position):
        return False

    # Check if target position has an item already
    if state.item_map[state.player_level, target_position[0], target_position[1]] != 0:
        return False

    # Place the furnace by moving to the position and pressing the appropriate key
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)

        # Move to target position
        direction = 0
        if target_position[1] > state.player_position[1]:
            direction = 1
        elif target_position[1] < state.player_position[1]:
            direction = -1
        elif target_position[0] > state.player_position[0]:
            direction = 2
        elif target_position[0] < state.player_position[0]:
            direction = 3

        if direction != 0:
            _, new_state, reward, done, info = state.step(
                key, state, direction, state.default_params
            )
            state = new_state

        # Place the furnace
        action = Action.PLACE_FURNACE.value
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

        # Check if furnace was placed
        if (
            state.map[state.player_level, target_position[0], target_position[1]]
            == BlockType.FURNACE.value
        ):
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
