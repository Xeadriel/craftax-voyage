# Description:
# Places a specified block at a target position.
# Returns True if successfully placed, False otherwise.
# Assumes the target position is within 5 blocks of the player and is on valid ground.

from craftax.craftax.constants import (
    Action,
    BlockType,
    CAN_PLACE_ITEM_BLOCKS,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_solid_block,
)


def place_block(env_step, state, block_name, target_position, max_steps=15):
    """
    Places a specified block at a target position.

    Args:
        env_step: The environment step function
        state: Current environment state
        block_name: Name of block to place (e.g., "stone", "torch")
        target_position: [x, y] coordinates of target position
        max_steps: Maximum number of steps to attempt placement

    Returns:
        True if successfully placed, False otherwise
    """
    # Check if target position is valid for placement
    if not (
        0 <= target_position[0] < state.map[state.player_level].shape[0]
        and 0 <= target_position[1] < state.map[state.player_level].shape[1]
    ):
        raise ValueError(f"Target position {target_position} is out of bounds")

    # Check if target is on valid ground (grass, path, etc.)
    target_block = state.map[state.player_level][target_position[0], target_position[1]]
    if target_block not in CAN_PLACE_ITEM_BLOCKS:
        raise ValueError(
            f"Cannot place block on {BlockType(target_block).name} - must be on grass, path, or similar"
        )

    # Check if target is solid
    if is_in_solid_block(state, target_position):
        raise ValueError(f"Cannot place block on solid block {target_position}")

    # Move to target position
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_position == target_position:
            break
        if state.player_health <= 0:
            raise ValueError("Player died while moving to placement position")

    # Place the block
    for _ in range(max_steps):
        # Use appropriate placement action based on block type
        if block_name == "stone":
            state = env_step(None, state, Action.PLACE_STONE.value, None)
        elif block_name == "torch":
            state = env_step(None, state, Action.PLACE_TORCH.value, None)
        elif block_name == "table":
            state = env_step(None, state, Action.PLACE_TABLE.value, None)
        elif block_name == "furnace":
            state = env_step(None, state, Action.PLACE_FURNACE.value, None)
        elif block_name == "plant":
            state = env_step(None, state, Action.PLACE_PLANT.value, None)
        else:
            state = env_step(None, state, Action.DO.value, None)

        if state.player_health <= 0:
            raise ValueError("Player died while placing block")

    return True
