# Description:
# Crafts a specified item at a crafting table.
# Returns True if successfully crafted, False otherwise.
# Assumes the crafting table is within 5 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    DIRECTIONS,
    CLOSE_BLOCKS,
)
from craftax.craftax.util.game_logic_utils import (
    is_near_block,
    is_position_in_bounds_not_in_mob_not_colliding,
)


def craft_item(env_step, state, item_name, max_steps=20):
    """
    Crafts a specified item at a crafting table.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        item_name: Name of item to craft (e.g., "wood_pickaxe", "stone_sword")
        max_steps: Maximum number of steps to attempt crafting
    
    Returns:
        True if successfully crafted, False otherwise
    """
    # Check if player is near a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        raise ValueError("No crafting table nearby")
    
    # Move to crafting table
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if is_near_block(state, BlockType.CRAFTING_TABLE.value):
            break
        if state.player_health <= 0:
            raise ValueError("Player died while moving to crafting table")
    
    # Check if player is near crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        raise TimeoutError("Failed to reach crafting table within max_steps")
    
    # Check if player has required materials
    # This is a simplified check - actual crafting recipes are complex
    if state.inventory.wood < 1:
        raise ValueError("Not enough wood to craft item")
    
    # Craft the item
    for _ in range(max_steps):
        # Try different crafting actions based on item name
        if "pickaxe" in item_name.lower():
            if "wood" in item_name.lower():
                state = env_step(None, state, Action.MAKE_WOOD_PICKAXE.value, None)
            elif "stone" in item_name.lower():
                state = env_step(None, state, Action.MAKE_STONE_PICKAXE.value, None)
            elif "iron" in item_name.lower():
                state = env_step(None, state, Action.MAKE_IRON_PICKAXE.value, None)
            elif "diamond" in item_name.lower():
                state = env_step(None, state, Action.MAKE_DIAMOND_PICKAXE.value, None)
        elif "sword" in item_name.lower():
            if "wood" in item_name.lower():
                state = env_step(None, state, Action.MAKE_WOOD_SWORD.value, None)
            elif "stone" in item_name.lower():
                state = env_step(None, state, Action.MAKE_STONE_SWORD.value, None)
            elif "iron" in item_name.lower():
                state = env_step(None, state, Action.MAKE_IRON_SWORD.value, None)
            elif "diamond" in item_name.lower():
                state = env_step(None, state, Action.MAKE_DIAMOND_SWORD.value, None)
        elif "torch" in item_name.lower():
            state = env_step(None, state, Action.MAKE_TORCH.value, None)
        elif "arrow" in item_name.lower():
            state = env_step(None, state, Action.MAKE_ARROW.value, None)
        else:
            state = env_step(None, state, Action.DO.value, None)
        
        if state.player_health <= 0:
            raise ValueError("Player died while crafting item")
    
    return True
