# Description:
# Explores the environment until a specified condition is met.
# Returns True if condition was met, False otherwise.
# Uses pathfinding to navigate towards the condition.

from craftax.craftax.constants import (
    Action,
    SOLID_BLOCKS,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_position_in_bounds_not_in_mob_not_colliding,
    is_in_solid_block,
)


def explore_until(env_step, state, condition_func, max_steps=100):
    """
    Explores the environment until a condition is met.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        condition_func: Function that takes state and returns True if condition met
        max_steps: Maximum number of steps to explore
    
    Returns:
        True if condition was met, False otherwise
    """
    steps_taken = 0
    
    while steps_taken < max_steps:
        # Check if condition is met
        if condition_func(state):
            return True
        
        # Calculate direction to move
        current_position = state.player_position
        
        # Find the direction that gets us to a new area
        best_direction = None
        best_distance = float('inf')
        
        for direction in DIRECTIONS[1:5]:  # Skip NOOP
            proposed = current_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                # Check if this is a new area (not immediately adjacent to current)
                distance = (proposed[0] - current_position[0])**2 + (proposed[1] - current_position[1])**2
                if distance > 1 and distance < best_distance:
                    best_distance = distance
                    best_direction = direction
        
        if best_direction is None:
            raise ValueError("Cannot explore further - no valid path")
        
        # Move in the best direction
        state = env_step(None, state, best_direction.value, None)
        steps_taken += 1
        
        # Check if player died
        if state.player_health <= 0:
            raise ValueError("Player died while exploring")
    
    raise TimeoutError(f"Failed to meet condition within {max_steps} steps")
