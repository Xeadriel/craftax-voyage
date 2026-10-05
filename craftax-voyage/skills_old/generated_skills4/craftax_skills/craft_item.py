# Description:
# Crafts a specific item at a crafting table or furnace.
# Returns True if successful, False if crafting table/furnace not found or insufficient materials.
# Handles both crafting table and furnace-based recipes.

def craft_item(state, item_name, max_steps=100):
    """
    Craft a specific item.
    
    Args:
        state: Current environment state
        item_name: Name of item to craft (e.g., "wood_pickaxe", "stone_sword")
        max_steps: Maximum steps to find crafting table and craft (default 100)
    
    Returns:
        bool: True if item crafted, False otherwise
    """
    from craftax.craftax.constants import Action, DIRECTIONS, is_near_block, BlockType
    from craftax.craftax.game_logic import do_crafting
    
    # Map item names to action codes
    item_to_action = {
        "wood_pickaxe": Action.MAKE_WOOD_PICKAXE,
        "stone_pickaxe": Action.MAKE_STONE_PICKAXE,
        "iron_pickaxe": Action.MAKE_IRON_PICKAXE,
        "diamond_pickaxe": Action.MAKE_DIAMOND_PICKAXE,
        "wood_sword": Action.MAKE_WOOD_SWORD,
        "stone_sword": Action.MAKE_STONE_SWORD,
        "iron_sword": Action.MAKE_IRON_SWORD,
        "diamond_sword": Action.MAKE_DIAMOND_SWORD,
        "iron_armour": Action.MAKE_IRON_ARMOUR,
        "diamond_armour": Action.MAKE_DIAMOND_ARMOUR,
        "arrow": Action.MAKE_ARROW,
        "torch": Action.MAKE_TORCH,
    }
    
    if item_name not in item_to_action:
        raise ValueError(f"Unknown item: {item_name}")
    
    action = item_to_action[item_name]
    
    # Check if we have required materials (basic checks)
    if action == Action.MAKE_WOOD_PICKAXE:
        if state.inventory.wood < 1:
            raise ValueError("Cannot craft wood pickaxe - need wood")
    elif action == Action.MAKE_STONE_PICKAXE:
        if state.inventory.wood < 1 or state.inventory.stone < 1:
            raise ValueError("Cannot craft stone pickaxe - need wood and stone")
    elif action == Action.MAKE_IRON_PICKAXE:
        if state.inventory.wood < 1 or state.inventory.stone < 1 or state.inventory.iron < 1 or state.inventory.coal < 1:
            raise ValueError("Cannot craft iron pickaxe - need wood, stone, iron, and coal")
    elif action == Action.MAKE_DIAMOND_PICKAXE:
        if state.inventory.wood < 1 or state.inventory.diamond < 3:
            raise ValueError("Cannot craft diamond pickaxe - need wood and 3 diamonds")
    elif action == Action.MAKE_WOOD_SWORD:
        if state.inventory.wood < 1:
            raise ValueError("Cannot craft wood sword - need wood")
    elif action == Action.MAKE_STONE_SWORD:
        if state.inventory.wood < 1 or state.inventory.stone < 1:
            raise ValueError("Cannot craft stone sword - need wood and stone")
    elif action == Action.MAKE_IRON_SWORD:
        if state.inventory.wood < 1 or state.inventory.stone < 1 or state.inventory.iron < 1 or state.inventory.coal < 1:
            raise ValueError("Cannot craft iron sword - need wood, stone, iron, and coal")
    elif action == Action.MAKE_DIAMOND_SWORD:
        if state.inventory.wood < 1 or state.inventory.diamond < 2:
            raise ValueError("Cannot craft diamond sword - need wood and 2 diamonds")
    elif action == Action.MAKE_IRON_ARMOUR:
        if state.inventory.iron < 3 or state.inventory.coal < 3:
            raise ValueError("Cannot craft iron armour - need 3 iron and 3 coal")
    elif action == Action.MAKE_DIAMOND_ARMOUR:
        if state.inventory.diamond < 3:
            raise ValueError("Cannot craft diamond armour - need 3 diamonds")
    elif action == Action.MAKE_ARROW:
        if state.inventory.wood < 1 or state.inventory.stone < 1:
            raise ValueError("Cannot craft arrow - need wood and stone")
    elif action == Action.MAKE_TORCH:
        if state.inventory.wood < 1 or state.inventory.coal < 1:
            raise ValueError("Cannot craft torch - need wood and coal")
    
    # Find crafting table or furnace
    crafting_table_found = False
    furnace_found = False
    
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if state.map[state.player_level, block_pos[0], block_pos[1]] == BlockType.CRAFTING_TABLE.value:
                    crafting_table_found = True
                    break
                elif state.map[state.player_level, block_pos[0], block_pos[1]] == BlockType.FURNACE.value:
                    furnace_found = True
                    break
        if crafting_table_found or furnace_found:
            break
    
    if not crafting_table_found and not furnace_found:
        raise ValueError("Cannot find crafting table or furnace nearby")
    
    # Move to crafting table or furnace
    target_block = None
    if crafting_table_found:
        target_block = BlockType.CRAFTING_TABLE
    else:
        target_block = BlockType.FURNACE
    
    dx = target_block[0] - state.player_position[0]
    dy = target_block[1] - state.player_position[1]
    
    steps_taken = 0
    while steps_taken < max_steps:
        if abs(dx) <= 1 and abs(dy) <= 1:
            if dx == 1:
                move_dir = Action.RIGHT
            elif dx == -1:
                move_dir = Action.LEFT
            elif dy == 1:
                move_dir = Action.DOWN
            elif dy == -1:
                move_dir = Action.UP
            
            state = state.replace(
                player_position=state.player_position + DIRECTIONS[move_dir.value],
                player_direction=move_dir.value
            )
            break
        
        if abs(dx) >= abs(dy):
            if dx > 0:
                move_dir = Action.RIGHT
            else:
                move_dir = Action.LEFT
        else:
            if dy > 0:
                move_dir = Action.DOWN
            else:
                move_dir = Action.UP
        
        proposed_position = state.player_position + DIRECTIONS[move_dir.value]
        
        if not in_bounds(state, proposed_position):
            raise ValueError(f"Cannot reach crafting table - out of bounds")
        
        if is_in_solid_block(state, proposed_position):
            raise ValueError(f"Cannot reach crafting table - solid block at {proposed_position}")
        
        if is_in_mob(state, proposed_position):
            raise ValueError(f"Cannot reach crafting table - mob at {proposed_position}")
        
        state = state.replace(
            player_position=proposed_position,
            player_direction=move_dir.value
        )
        
        dx = target_block[0] - state.player_position[0]
        dy = target_block[1] - state.player_position[1]
        steps_taken += 1
    
    # Craft the item
    state = do_crafting(state, action)
    
    return True
