# Description:
# Enchants a specified item at an enchantment table.
# Returns True if successfully enchanted, False otherwise.
# Assumes the enchantment table is within 5 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_near_block,
    is_position_in_bounds_not_in_mob_not_colliding,
)


def enchant_item(env_step, state, item_name, enchantment_type, max_steps=15):
    """
    Enchants a specified item.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        item_name: Name of item to enchant (e.g., "sword", "bow", "helmet")
        enchantment_type: "fire" or "ice"
        max_steps: Maximum number of steps to attempt enchanting
    
    Returns:
        True if successfully enchanted, False otherwise
    """
    # Check if player has enough mana
    if state.player_mana < 9:
        raise ValueError("Not enough mana to enchant item")
    
    # Check if player has the required gem
    if enchantment_type == "fire" and state.inventory.ruby < 1:
        raise ValueError("Not enough rubies to enchant item")
    if enchantment_type == "ice" and state.inventory.sapphire < 1:
        raise ValueError("Not enough sapphires to enchant item")
    
    # Move to enchantment table
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or \
           is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value):
            break
        if state.player_health <= 0:
            raise ValueError("Player died while moving to enchantment table")
    
    # Enchant the item
    for _ in range(max_steps):
        if enchantment_type == "fire":
            if item_name == "sword":
                state = env_step(None, state, Action.ENCHANT_SWORD.value, None)
            elif item_name == "bow":
                state = env_step(None, state, Action.ENCHANT_BOW.value, None)
            elif item_name == "helmet":
                state = env_step(None, state, Action.ENCHANT_ARMOUR.value, None)
        else:
            if item_name == "sword":
                state = env_step(None, state, Action.ENCHANT_SWORD.value, None)
            elif item_name == "bow":
                state = env_step(None, state, Action.ENCHANT_BOW.value, None)
            elif item_name == "helmet":
                state = env_step(None, state, Action.ENCHANT_ARMOUR.value, None)
        
        if state.player_health <= 0:
            raise ValueError("Player died while enchanting item")
    
    return True
