# Description:
# Opens a chest at a specified position and collects items.
# Returns True if chest was opened, False otherwise.
# Assumes the chest is within 5 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_near_block,
    is_position_in_bounds_not_in_mob_not_colliding,
)


def open_chest(env_step, state, chest_position, max_steps=15):
    """
    Opens a chest at a specified position.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        chest_position: [x, y] coordinates of chest
        max_steps: Maximum number of steps to attempt opening
    
    Returns:
        True if chest was opened, False otherwise
    """
    # Check if chest is within bounds
    if not (0 <= chest_position[0] < state.map[state.player_level].shape[0] and
            0 <= chest_position[1] < state.map[state.player_level].shape[1]):
        raise ValueError(f"Chest position {chest_position} is out of bounds")
    
    # Check if chest is at the target position
    if state.map[state.player_level][chest_position[0], chest_position[1]] != BlockType.CHEST.value:
        raise ValueError(f"Not a chest at {chest_position}")
    
    # Move to chest position
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_position == chest_position:
            break
        if state.player_health <= 0:
            raise ValueError("Player died while moving to chest")
    
    # Check if we're at the chest
    if state.player_position != chest_position:
        raise TimeoutError(f"Failed to reach chest {chest_position} within {max_steps} steps")
    
    # Open the chest
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while opening chest")
    
    return True
