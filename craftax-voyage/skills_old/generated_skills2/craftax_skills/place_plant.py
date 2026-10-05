# Skill: place_plant
# Purpose: Places a sapling on grass
# Required inputs: target_position (tuple), max_steps (int)
# Preconditions: Player must be near the target position, have a sapling in inventory
# Expected effects: Sapling is placed on grass, inventory updated
# Failure conditions: Invalid position, no sapling in inventory, not on grass
# Explanation: Uses state.map for grass detection, state.inventory for sapling availability,
#             Action.PLACE_PLANT for sapling placement

import jax
import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import in_bounds, is_in_solid_block

def place_plant(state: EnvState, target_position: tuple, max_steps: int = 100) -> bool:
    """
    Places a sapling on grass.
    
    Returns True if sapling was placed, False otherwise.
    """
    # Check if we have a sapling in inventory
    if state.inventory.sapling <= 0:
        return False
    
    # Check if target position is in bounds
    if not in_bounds(state, target_position):
        return False
    
    # Check if target position is grass
    if state.map[state.player_level, target_position[0], target_position[1]] != BlockType.GRASS.value:
        return False
    
    # Check if target position has an item already
    if state.item_map[state.player_level, target_position[0], target_position[1]] != 0:
        return False
    
    # Place the sapling by moving to the position and pressing the appropriate key
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
            _, new_state, reward, done, info = state.step(key, state, direction, state.default_params)
            state = new_state
        
        # Place the sapling
        action = Action.PLACE_PLANT.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if sapling was placed
        if state.map[state.player_level, target_position[0], target_position[1]] == BlockType.PLANT.value:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
