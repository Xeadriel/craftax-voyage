# Skill: place_crafting_table
# Purpose: Places a crafting table
# Required inputs: target_position (tuple), max_steps (int)
# Preconditions: Player must be near the target position, have 2 wood in inventory
# Expected effects: Crafting table is placed at target position, inventory updated
# Failure conditions: Invalid position, no wood in inventory, solid block at target
# Explanation: Uses state.map for block placement validation, state.inventory for wood availability,
#             Action.PLACE_TABLE for table placement

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import in_bounds, is_in_solid_block


def place_crafting_table(
    state: EnvState, target_position: tuple, max_steps: int = 100
) -> bool:
    """
    Places a crafting table.

    Returns True if table was placed, False otherwise.
    """
    # Check if we have 2 wood in inventory
    if state.inventory.wood < 2:
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

    # Place the table by moving to the position and pressing the appropriate key
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

        # Place the table
        action = Action.PLACE_TABLE.value
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

        # Check if table was placed
        if (
            state.map[state.player_level, target_position[0], target_position[1]]
            == BlockType.CRAFTING_TABLE.value
        ):
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
