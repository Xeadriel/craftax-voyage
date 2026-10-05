# Skill: enchant_item
# Purpose: Enchants a specified item
# Required inputs: item_type (string), enchantment_type (int), max_steps (int)
# Preconditions: Player must be at an enchantment table, have gem and mana
# Expected effects: Item is enchanted, mana consumed, gem consumed
# Failure conditions: No enchantment table, insufficient mana/gem, invalid item
# Explanation: Uses state.map for enchantment table detection, state.inventory for gem availability,
#             state.player_mana for mana tracking, Action.ENCHANT_* for enchanting interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def enchant_item(state: EnvState, item_type: str, enchantment_type: int, max_steps: int = 100) -> bool:
    """
    Enchants a specified item.
    
    Returns True if item was enchanted, False otherwise.
    """
    # Define enchantment types
    enchantment_types = {
        "fire": 1,
        "ice": 2,
    }
    
    type_index = enchantment_types.get(enchantment_type)
    if type_index is None:
        return False
    
    # Check if we have the required gem
    gem_type = "sapphire" if type_index == 2 else "ruby"
    gem_amount = getattr(state.inventory, gem_type)
    if gem_amount <= 0:
        return False
    
    # Check if we have 9 mana
    if state.player_mana < 9:
        return False
    
    # Find an enchantment table
    if not is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value):
        return False
    
    # Check if we're at an enchantment table
    if not is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value):
        return False
    
    # Enchant the item by pressing the appropriate key
    enchant_keys = {
        "sword": Action.ENCHANT_SWORD.value,
        "bow": Action.ENCHANT_BOW.value,
        "armour": Action.ENCHANT_ARMOUR.value,
    }
    
    enchant_key = enchant_keys.get(item_type)
    if not enchant_key:
        return False
    
    # Enchant the item
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Move to enchantment table
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
        
        # Enchant
        action = enchant_key
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if item was enchanted
        if item_type == "sword" and state.sword_enchantment == type_index:
            return True
        elif item_type == "bow" and state.bow_enchantment == type_index:
            return True
        elif item_type == "armour" and state.armour_enchantments[0] == type_index:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
