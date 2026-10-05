# Description:
# Mines a specified block type if the player has the required tool level.
# Checks inventory for required pickaxe level before attempting to mine.
# Returns True if mining was successful, False otherwise.

def mine_block(state, action, step_func):
    """
    Mines a block at the player's current facing direction.
    
    Args:
        state: Current game state
        action: Action enum value (Action.DO for mining)
        step_func: Step function to execute actions
    
    Returns:
        True if mining was successful, False otherwise
    """
    # Check if player is at a valid block position
    block_position = state.player_position + DIRECTIONS[state.player_direction]
    action_block_in_bounds = in_bounds(state, block_position)
    
    if not action_block_in_bounds:
        return False
    
    # Check if player is not attacking a mob
    did_attack_mob = is_in_mob(state, block_position)
    if did_attack_mob:
        return False
    
    # Get the block type at the target position
    target_block = state.map[state.player_level, block_position[0], block_position[1]]
    
    # Check if it's a mineable block
    if target_block == BlockType.TREE.value:
        # Trees can be mined by any tool
        step_func(Action.DO)
        return True
    
    elif target_block == BlockType.STONE.value:
        # Stone requires pickaxe level >= 1
        if state.inventory.pickaxe >= 1:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.COAL.value:
        # Coal requires pickaxe level >= 1
        if state.inventory.pickaxe >= 1:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.IRON.value:
        # Iron requires pickaxe level >= 2
        if state.inventory.pickaxe >= 2:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.DIAMOND.value:
        # Diamond requires pickaxe level >= 3
        if state.inventory.pickaxe >= 3:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.SAPPHIRE.value:
        # Sapphire requires pickaxe level >= 4
        if state.inventory.pickaxe >= 4:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.RUBY.value:
        # Ruby requires pickaxe level >= 4
        if state.inventory.pickaxe >= 4:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.STALAGMITE.value:
        # Stalagmite requires pickaxe level >= 1
        if state.inventory.pickaxe >= 1:
            step_func(Action.DO)
            return True
        else:
            return False
    
    elif target_block == BlockType.CHEST.value:
        # Chests can be opened
        step_func(Action.DO)
        return True
    
    else:
        # Cannot mine this block type
        return False
