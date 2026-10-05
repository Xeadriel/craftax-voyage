# Description:
# Explores the environment in a specified direction until a condition is met or max steps reached.
# Checks for mobs and returns early if enemies are detected.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_mob,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def explore(env_step_fn, state, direction: int, max_steps: int = 100, check_condition: callable = None):
    """
    Explores the environment in a specified direction until a condition is met or max steps reached.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        direction: Direction to explore (UP, DOWN, LEFT, RIGHT)
        max_steps: Maximum number of steps to explore
        check_condition: Optional callback function that returns True when exploration should stop
    
    Returns:
        True if exploration was successful
    
    Raises:
        ValueError: If direction is invalid, no valid path, or exploration failed
    """
    import jax.numpy as jnp
    
    # Validate direction
    valid_directions = [Action.UP.value, Action.DOWN.value, Action.LEFT.value, Action.RIGHT.value]
    if direction not in valid_directions:
        raise ValueError(f"Invalid direction {direction}. Must be one of {valid_directions}")
    
    # Check if we're already at the target condition
    if check_condition is not None:
        if check_condition(state):
            return True
    
    # Explore in the specified direction
    for step in range(max_steps):
        # Check for mobs in the direction
        proposed_pos = state.player_position + DIRECTIONS[direction]
        
        if not in_bounds(state, proposed_pos):
            raise ValueError(f"Cannot move in direction {direction} - out of bounds")
        
        if is_in_mob(state, proposed_pos):
            raise ValueError(f"Cannot move in direction {direction} - mob in the way")
        
        # Check if we can move
        if not is_position_in_bounds_not_in_mob_not_colliding(state, proposed_pos, COLLISION_LAND_CREATURE):
            raise ValueError(f"Cannot move in direction {direction} - blocked")
        
        # Execute move
        env_step_fn(state, direction)
        state = state.replace(
            player_position=state.player_position + DIRECTIONS[direction],
            player_direction=direction
        )
        
        # Check if we reached the target condition
        if check_condition is not None:
            if check_condition(state):
                return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Exploration failed after multiple attempts")
    
    raise ValueError("Exploration failed after reaching max steps")
