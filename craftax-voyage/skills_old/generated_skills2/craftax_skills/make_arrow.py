# Skill: make_arrow
# Purpose: Crafts arrows
# Required inputs: count (int), max_steps (int)
# Preconditions: Player must be at a crafting table, have wood and stone
# Expected effects: Arrows are crafted and added to inventory, materials consumed
# Failure conditions: No crafting table, insufficient materials
# Explanation: Uses state.map for crafting table detection, state.inventory for materials,
#             Action.MAKE_ARROW for crafting interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def make_arrow(state: EnvState, count: int, max_steps: int = 100) -> bool:
    """
    Crafts arrows.
    
    Returns True if arrows were crafted, False otherwise.
    """
    # Check if we have required materials
    if state.inventory.wood <= 0 or state.inventory.stone <= 0:
        return False
    
    # Find a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False
    
    # Check if we're at a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False
    
    # Craft arrows by pressing MAKE_ARROW key
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Move to crafting table
        direction = 0
        if state.player_position[1] > state.player_position[1]:
            direction = 1
        elif state.player_position[1] < state.player_position[1]:
            direction = -1
        elif state.player_position[0] > state.player_position[0]:
            direction = 2
        elif state.player_position[0] < state.player_position[0]:
            direction = 3
        
        if direction != 0:
            _, new_state, reward, done, info = state.step(key, state, direction, state.default_params)
            state = new_state
        
        # Craft
        action = Action.MAKE_ARROW.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if arrows were crafted
        if state.inventory.arrows >= count:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
