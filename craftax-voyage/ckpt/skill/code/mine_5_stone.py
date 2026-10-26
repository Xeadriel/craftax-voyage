def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType, Action
    
    # Check if we already have a pickaxe
    if state.inventory.pickaxe > 0:
        log_fn("Already have a pickaxe")
    else:
        # Need to craft a wood pickaxe first
        log_fn("Crafting a wood pickaxe")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)
    
    # Check if we have enough stone already
    if state.inventory.stone >= 5:
        log_fn(f"Already have {state.inventory.stone} stone, task complete")
        return state
    
    # Need to mine more stone
    stones_needed = 5 - state.inventory.stone
    
    log_fn(f"Need to mine {stones_needed} more stone blocks")
    
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