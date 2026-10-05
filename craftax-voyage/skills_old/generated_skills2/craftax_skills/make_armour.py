# Skill: make_armour
# Purpose: Crafts armour of specified level
# Required inputs: armour_level (int), max_steps (int)
# Preconditions: Player must be at a crafting table and furnace, have required materials
# Expected effects: Armour is crafted and added to inventory, materials consumed
# Failure conditions: No crafting table/furnace, insufficient materials, invalid level
# Explanation: Uses state.map for crafting table and furnace detection, state.inventory for materials,
#             Action.MAKE_* for crafting interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def make_armour(state: EnvState, armour_level: int, max_steps: int = 100) -> bool:
    """
    Crafts armour of specified level.
    
    Returns True if armour was crafted, False otherwise.
    """
    # Define armour crafting recipes
    armour_recipes = {
        1: {"iron": 3, "coal": 3, "armour": 0},
        2: {"diamond": 3, "armour": 0},
    }
    
    recipe = armour_recipes.get(armour_level)
    if not recipe:
        return False
    
    # Check if we have required materials
    for material, amount in recipe.items():
        if amount > 0:
            current_amount = getattr(state.inventory, material)
            if current_amount < amount:
                return False
    
    # Find a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False
    
    # Find a furnace
    if not is_near_block(state, BlockType.FURNACE.value):
        return False
    
    # Check if we're at a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False
    
    # Craft the armour by pressing the appropriate key
    craft_keys = {
        1: Action.MAKE_IRON_ARMOUR.value,
        2: Action.MAKE_DIAMOND_ARMOUR.value,
    }
    
    craft_key = craft_keys.get(armour_level)
    if not craft_key:
        return False
    
    # Craft the armour
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
        action = craft_key
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if armour was crafted
        if state.inventory.armour[0] >= armour_level or state.inventory.armour[1] >= armour_level:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
