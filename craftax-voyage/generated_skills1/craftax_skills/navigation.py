# Description:
# Provides reusable navigation skills for moving between floors and locations.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step
from craftax.craftax.util.game_logic_utils import *

def descend_floor(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Descends to the next floor using a ladder.
    Returns True if descent was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DESCEND.value:
            return False
        
        # Check if at down ladder
        if state.item_map[state.player_level, state.player_position[0], state.player_position[1]] != ItemType.LADDER_DOWN.value:
            return False
        
        # Check if monsters have been killed enough to open ladder
        if state.monsters_killed[state.player_level] < MONSTERS_KILLED_TO_CLEAR_LEVEL:
            return False
        
        # Check if not at last floor
        if state.player_level >= StaticEnvParams().num_levels - 1:
            return False
        
        state = craftax_step(state.state_rng, state, Action.DESCEND.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def ascend_floor(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Ascends to the previous floor using a ladder.
    Returns True if ascent was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.ASCEND.value:
            return False
        
        # Check if at up ladder
        if state.item_map[state.player_level, state.player_position[0], state.player_position[1]] != ItemType.LADDER_UP.value:
            return False
        
        # Check if not at first floor
        if state.player_level <= 0:
            return False
        
        state = craftax_step(state.state_rng, state, Action.ASCEND.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def navigate_to_floor(state: EnvState, action_func, target_floor: int, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Navigates to a specific floor.
    Returns True if navigation was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at down ladder
        if state.item_map[state.player_level, state.player_position[0], state.player_position[1]] == ItemType.LADDER_DOWN.value:
            if state.player_level < target_floor:
                state = craftax_step(state.state_rng, state, Action.DESCEND.value, EnvParams(), StaticEnvParams())
                return True
        
        # Check if at up ladder
        if state.item_map[state.player_level, state.player_position[0], state.player_position[1]] == ItemType.LADDER_UP.value:
            if state.player_level > target_floor:
                state = craftax_step(state.state_rng, state, Action.ASCEND.value, EnvParams(), StaticEnvParams())
                return True
        
        # Check if already at target floor
        if state.player_level == target_floor:
            return True
        
        # Move in direction
        direction = action_func
        if direction == Action.LEFT.value:
            direction = (state.player_direction - 1) % 5
        elif direction == Action.RIGHT.value:
            direction = (state.player_direction + 1) % 5
        elif direction == Action.UP.value:
            direction = (state.player_direction + 2) % 5
        elif direction == Action.DOWN.value:
            direction = (state.player_direction + 3) % 5
        
        # Check if direction is valid
        if direction < 0 or direction >= 5:
            return False
        
        # Move to new position
        new_position = state.player_position + DIRECTIONS[direction]
        
        # Check bounds
        if not in_bounds(state, new_position):
            return False
        
        # Check for mob
        if is_in_mob(state, new_position):
            return False
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False
