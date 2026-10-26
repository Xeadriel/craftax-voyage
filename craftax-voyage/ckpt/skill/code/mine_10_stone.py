def mine_10_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we already have 10 stone
    if state.inventory.stone >= 10:
        log_fn(f"Already have {state.inventory.stone} stone, task complete")
        return state
    
    # Need to mine more stone
    stones_needed = 10 - state.inventory.stone
    
    log_fn(f"Need to mine {stones_needed} more stone blocks")
    
    for i in range(stones_needed):
        log_fn(f"Mining stone {i+1}/{stones_needed}")
        
        # Explore until we can see a stone block
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        
        # Mine the stone block
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
        
        # Check if we have enough stone now
        if state.inventory.stone >= 10:
            log_fn(f"Reached target: {state.inventory.stone} stone")
            break
    
    return state