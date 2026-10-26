def obtain_5_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we already have 5 wood
    if state.inventory.wood >= 5:
        log_fn(f"Already have {state.inventory.wood} wood, task complete")
        return state
    
    # Need to mine more wood
    wood_needed = 5 - state.inventory.wood
    
    log_fn(f"Need {wood_needed} more wood, have {state.inventory.wood}")
    
    # Mine trees until we have 5 wood
    for i in range(wood_needed):
        log_fn(f"Mining wood {i+1}/{wood_needed}")
        
        # Explore until we can see a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        # Mine the tree to get 1 wood
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Check if we have enough wood now
        if state.inventory.wood >= 5:
            log_fn(f"Reached target: {state.inventory.wood} wood")
            break
    
    return state