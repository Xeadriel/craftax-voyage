def craft_stone_pickaxe(state, log_fn, step_func):
    """
    Crafts 1 stone pickaxe if possible.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after crafting the stone pickaxe
    
    Raises:
        Exception: If we don't have enough wood or stone, or the crafting table is not nearby
    """
    # Check if we have enough wood (need 2 for crafting table + 1 for stone pickaxe = 3 total)
    if state.inventory.wood < 3:
        log_fn(f"Not enough wood to craft stone pickaxe (need 3, have {state.inventory.wood})")
        raise Exception(f"Not enough wood to craft stone pickaxe")
    
    # Check if we have enough stone
    if state.inventory.stone < 1:
        log_fn(f"Not enough stone to craft stone pickaxe (need 1, have {state.inventory.stone})")
        raise Exception(f"Not enough stone to craft stone pickaxe")
    
    # Check if we have a wood pickaxe (required to mine stone)
    if state.inventory.pickaxe == 0:
        log_fn("Need a wood pickaxe to mine stone")
        # Explore until we find a stone block
        from craftax.craftax.constants import BlockType
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    
    # Place a crafting table in front of the player
    # The player is facing LEFT, so the tile (-1, 0) is in front
    log_fn("Placing crafting table...")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed!")
    
    # Craft the stone pickaxe
    log_fn("Crafting stone pickaxe...")
    state = craft(state, log_fn, step_func, "stone_pickaxe", number=1)
    log_fn("Successfully crafted stone pickaxe!")
    
    return state