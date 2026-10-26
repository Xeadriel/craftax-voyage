def mine_5_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Mining 5 wood")
    
    # Check if we already have 5 wood
    if state.inventory.wood >= 5:
        log_fn(f"Already have {state.inventory.wood} wood, task complete")
        return state
    
    # Need to mine more wood
    wood_needed = 5 - state.inventory.wood
    
    log_fn(f"Need to mine {wood_needed} more wood blocks, currently have {state.inventory.wood}")
    
    # Mine trees until we have 5 wood
    for i in range(wood_needed):
        log_fn(f"Mining wood {i+1}/{wood_needed}")
        
        # Explore until we can see a tree
        log_fn("Exploring to find a tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=50)
        
        # Mine the tree to get 1 wood
        log_fn("Mining tree")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=10)
        
        # Check if we have enough wood now
        if state.inventory.wood >= 5:
            log_fn(f"Reached target: {state.inventory.wood} wood")
            break
    
    log_fn(f"Successfully mined 5 wood. Current inventory: {state.inventory.wood} wood")
    
    return state