# Description:
# Moves the player to a specified block position using pathfinding and collision avoidance.
# Returns True if successfully reached the block, False otherwise.
# Assumes the block is within 15 blocks of the player.

from craftax.craftax.constants import (
    Action,
    SOLID_BLOCKS,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_position_in_bounds_not_in_mob_not_colliding,
    is_in_solid_block,
)


def move_to_block(env_step, state, target_position, max_steps=30):
    """
    Moves the player to a specified block position.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        target_position: [x, y] coordinates of target block
        max_steps: Maximum number of steps to attempt movement
    
    Returns:
        True if successfully reached target, False otherwise
    """
    # Check if target is within bounds
    if not (0 <= target_position[0] < state.map[state.player_level].shape[0] and
            0 <= target_position[1] < state.map[state.player_level].shape[1]):
        raise ValueError(f"Target position {target_position} is out of bounds")
    
    # Check if target is solid (cannot walk through)
    if is_in_solid_block(state, target_position):
        raise ValueError(f"Cannot move to solid block {target_position}")
    
    # Check if target is in front of player
    player_direction = state.player_direction
    front_block = target_position + DIRECTIONS[player_direction]
    if front_block != target_position:
        raise ValueError(
            f"Target {target_position} is not in front of player (facing {player_direction})"
        )
    
    # Move towards target
    current_position = state.player_position
    steps_taken = 0
    
    while steps_taken < max_steps:
        # Check if we've reached the target
        if current_position == target_position:
            return True
        
        # Calculate direction to move
        dx = target_position[0] - current_position[0]
        dy = target_position[1] - current_position[1]
        
        # Find the direction that gets us closer
        best_direction = None
        best_distance = float('inf')
        
        for direction in DIRECTIONS[1:5]:  # Skip NOOP
            proposed = current_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                distance = (proposed[0] - target_position[0])**2 + (proposed[1] - target_position[1])**2
                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction
        
        if best_direction is None:
            raise ValueError(
                f"Cannot reach {target_position} - no valid path within {max_steps} steps"
            )
        
        # Move in the best direction
        state = env_step(None, state, best_direction.value, None)
        steps_taken += 1
        
        # Check if we're stuck
        if steps_taken > max_steps:
            raise TimeoutError(
                f"Could not reach {target_position} within {max_steps} steps"
            )
    
    raise TimeoutError(f"Failed to reach {target_position} within {max_steps} steps")
