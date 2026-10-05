# Description:
# Crafts a specified item at a crafting table or furnace.
# Checks inventory for required materials and proximity to crafting table/furnace.
# Returns True if crafting was successful, False otherwise.

def craft_item(state, action, step_func):
    """
    Crafts a specific item based on the action.
    
    Args:
        state: Current game state
        action: Action enum value (e.g., Action.MAKE_WOOD_PICKAXE)
        step_func: Step function to execute actions
    
    Returns:
        True if crafting was successful, False otherwise
    """
    # Check if player is near a crafting table
    is_at_crafting_table = is_near_block(state, BlockType.CRAFTING_TABLE.value)
    
    # Check if player is near a furnace
    is_at_furnace = is_near_block(state, BlockType.FURNACE.value)
    
    # Check if player is at a valid position to craft
    block_position = state.player_position + DIRECTIONS[state.player_direction]
    action_block_in_bounds = in_bounds(state, block_position)
    
    if not action_block_in_bounds:
        return False
    
    # Check if player is not attacking a mob
    did_attack_mob = is_in_mob(state, block_position)
    if did_attack_mob:
        return False
    
    # Check if player is at crafting table or furnace
    if not is_at_crafting_table and not is_at_furnace:
        return False
    
    # Check if player has enough materials
    # Wood Pickaxe
    if action == Action.MAKE_WOOD_PICKAXE.value:
        if state.inventory.wood >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Stone Pickaxe
    elif action == Action.MAKE_STONE_PICKAXE.value:
        if state.inventory.wood >= 1 and state.inventory.stone >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Iron Pickaxe
    elif action == Action.MAKE_IRON_PICKAXE.value:
        if state.inventory.wood >= 1 and state.inventory.stone >= 1 and \
           state.inventory.iron >= 1 and state.inventory.coal >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Diamond Pickaxe
    elif action == Action.MAKE_DIAMOND_PICKAXE.value:
        if state.inventory.wood >= 1 and state.inventory.diamond >= 3:
            step_func(Action.DO)
            return True
        return False
    
    # Wood Sword
    elif action == Action.MAKE_WOOD_SWORD.value:
        if state.inventory.wood >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Stone Sword
    elif action == Action.MAKE_STONE_SWORD.value:
        if state.inventory.stone >= 1 and state.inventory.wood >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Iron Sword
    elif action == Action.MAKE_IRON_SWORD.value:
        if state.inventory.wood >= 1 and state.inventory.stone >= 1 and \
           state.inventory.iron >= 1 and state.inventory.coal >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Diamond Sword
    elif action == Action.MAKE_DIAMOND_SWORD.value:
        if state.inventory.wood >= 1 and state.inventory.diamond >= 2:
            step_func(Action.DO)
            return True
        return False
    
    # Iron Armour
    elif action == Action.MAKE_IRON_ARMOUR.value:
        if state.inventory.iron >= 3 and state.inventory.coal >= 3:
            step_func(Action.DO)
            return True
        return False
    
    # Diamond Armour
    elif action == Action.MAKE_DIAMOND_ARMOUR.value:
        if state.inventory.diamond >= 3:
            step_func(Action.DO)
            return True
        return False
    
    # Arrow
    elif action == Action.MAKE_ARROW.value:
        if state.inventory.stone >= 1 and state.inventory.wood >= 1:
            step_func(Action.DO)
            return True
        return False
    
    # Torch
    elif action == Action.MAKE_TORCH.value:
        if state.inventory.coal >= 1 and state.inventory.wood >= 1:
            step_func(Action.DO)
            return True
        return False
    
    else:
        return False
