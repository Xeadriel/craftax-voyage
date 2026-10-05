# Description:
# Provides reusable movement skills for navigating the environment.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step
from craftax.craftax.util.game_logic_utils import *

def move_to_block(state: EnvState, action_func, block_type: BlockType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to a block of the specified type in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for block
        if state.map[state.player_level, new_position[0], new_position[1]] == block_type.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def move_to_ladder(state: EnvState, action_func, ladder_type: ItemType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to a ladder of the specified type in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for ladder
        if state.item_map[state.player_level, new_position[0], new_position[1]] == ladder_type.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def move_to_chest(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to a chest in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for chest
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.CHEST.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def move_to_enchantment_table(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to an enchantment table in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for enchantment table
        if state.map[state.player_level, new_position[0], new_position[1]] in [BlockType.ENCHANTMENT_TABLE_FIRE.value, BlockType.ENCHANTMENT_TABLE_ICE.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def move_to_furnace(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to a furnace in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for furnace
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.FURNACE.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def move_to_crafting_table(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Moves to a crafting table in the environment.
    Returns True if movement was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
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
        
        # Check for crafting table
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.CRAFTING_TABLE.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False
