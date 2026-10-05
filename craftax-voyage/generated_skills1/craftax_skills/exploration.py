# Description:
# Provides reusable exploration skills for finding resources, mobs, and locations.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step
from craftax.craftax.util.game_logic_utils import *

def find_resource(state: EnvState, action_func, resource_type: BlockType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a specific resource type in the environment.
    Returns True if resource was found and mined, False otherwise.
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
        
        # Check for resource
        if state.map[state.player_level, new_position[0], new_position[1]] == resource_type.value:
            # Mine the resource
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_mob(state: EnvState, action_func, mob_type: BlockType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a specific mob type in the environment.
    Returns True if mob was found and attacked, False otherwise.
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
            # Attack the mob
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_crafting_table(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a crafting table in the environment.
    Returns True if crafting table was found, False otherwise.
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
        
        # Check for crafting table
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.CRAFTING_TABLE.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_furnace(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a furnace in the environment.
    Returns True if furnace was found, False otherwise.
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
        
        # Check for furnace
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.FURNACE.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_chest(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a chest in the environment.
    Returns True if chest was found and opened, False otherwise.
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
        
        # Check for chest
        if state.map[state.player_level, new_position[0], new_position[1]] == BlockType.CHEST.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_ladder(state: EnvState, action_func, ladder_type: ItemType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for a ladder of the specified type in the environment.
    Returns True if ladder was found, False otherwise.
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
        
        # Check for ladder
        if state.item_map[state.player_level, new_position[0], new_position[1]] == ladder_type.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def find_enchantment_table(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Searches for an enchantment table in the environment.
    Returns True if enchantment table was found, False otherwise.
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
        
        # Check for enchantment table
        if state.map[state.player_level, new_position[0], new_position[1]] in [BlockType.ENCHANTMENT_TABLE_FIRE.value, BlockType.ENCHANTMENT_TABLE_ICE.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move to new position
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False
