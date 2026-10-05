# Description:
# Drinks water from a water source or fountain.
# Returns True if successfully drank water, False otherwise.
# Assumes a water source is within 5 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_position_in_bounds_not_in_mob_not_colliding,
)


def drink_water(env_step, state, max_steps=10):
    """
    Drinks water from a water source or fountain.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        max_steps: Maximum number of steps to attempt drinking
    
    Returns:
        True if successfully drank water, False otherwise
    """
    # Check if player is thirsty
    if state.player_drink >= 7 + 2 * state.player_dexterity:
        raise ValueError("Player is not thirsty")
    
    # Check for water source
    water_found = False
    for _ in range(max_steps):
        # Check all adjacent blocks
        for direction in DIRECTIONS[1:5]:
            proposed = state.player_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                block = state.map[state.player_level][proposed[0], proposed[1]]
                if block == BlockType.WATER.value or block == BlockType.FOUNTAIN.value:
                    water_found = True
                    break
        
        if water_found:
            break
        
        # Move towards water
        best_direction = None
        best_distance = float('inf')
        
        for direction in DIRECTIONS[1:5]:
            proposed = state.player_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                distance = (proposed[0] - state.player_position[0])**2 + (proposed[1] - state.player_position[1])**2
                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction
        
        if best_direction is None:
            raise ValueError("Cannot reach water source")
        
        state = env_step(None, state, best_direction.value, None)
    
    # Drink water
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while drinking water")
    
    return True
