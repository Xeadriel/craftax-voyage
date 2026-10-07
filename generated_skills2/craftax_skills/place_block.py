# Skill: place_block
# Purpose: Places a specified block at a target position
# Required inputs: block_type (BlockType enum), target_position (tuple), max_steps (int)
# Preconditions: Player must be near the target position, have the block in inventory
# Expected effects: Block is placed at target position, inventory updated
# Failure conditions: Invalid position, no block in inventory, solid block at target
# Explanation: Uses state.map for block placement validation, state.inventory for block availability,
#             state.player_position for movement, Action.PLACE_* for placement

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import in_bounds, is_in_solid_block


def place_block(
    state: EnvState, block_type: BlockType, target_position: tuple, max_steps: int = 100
) -> bool:
    """
    Places a specified block at a target position.

    Returns True if placement succeeded, False otherwise.
    """
    # Check if we have the block in inventory
    if block_type.value == BlockType.STONE.value:
        if state.inventory.stone <= 0:
            return False
    elif block_type.value == BlockType.TORCH.value:
        if state.inventory.torches <= 0:
            return False
    elif block_type.value == BlockType.PLANT.value:
        if state.inventory.sapling <= 0:
            return False
    else:
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

    # Place the block by moving to the position and pressing the appropriate key
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

        # Place the block
        action = Action.NOOP.value
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

        # Check if block was placed
        if (
            state.map[state.player_level, target_position[0], target_position[1]]
            == block_type.value
        ):
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
