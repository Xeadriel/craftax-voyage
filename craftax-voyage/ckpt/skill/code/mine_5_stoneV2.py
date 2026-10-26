def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check if we already have 5 stone
    if state.inventory.stone >= 5:
        log_fn(f"Already have {state.inventory.stone} stone, task complete")
        return state
    
    # Check if we have a pickaxe
    if state.inventory.pickaxe < 1:
        log_fn("Need a pickaxe to mine stone")
        
        # Need 1 wood for wood pickaxe
        if state.inventory.wood < 1:
            log_fn("Need wood to craft pickaxe")
            # Mine a tree
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Craft wood pickaxe (craft function places table if needed)
        log_fn("Crafting wood pickaxe")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)
    
    # Now mine 5 stone blocks
    stones_needed = 5 - state.inventory.stone
    
    for i in range(stones_needed):
        log_fn(f"Mining stone {i+1}/{stones_needed}")
        
        # Explore until we can see a stone block
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        
        # Mine the stone block
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
        
        # Check if we have enough stone now
        if state.inventory.stone >= 5:
            log_fn(f"Reached target: {state.inventory.stone} stone")
            break
    
    return state