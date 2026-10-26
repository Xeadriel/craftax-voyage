def mine_10_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Get current wood count
    current_wood = state.inventory.wood
    log_fn(f"Current wood: {current_wood}, need to mine {10 - current_wood} more trees")
    
    # Mine trees until we have 10 wood
    for i in range(10 - current_wood):
        # Explore until we find a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        log_fn(f"Mined tree {i+1}: Found tree and mined it")
        
        # Mine the tree
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        log_fn(f"Current wood after mining: {state.inventory.wood}")
        
        # Check if we've reached the goal
        if state.inventory.wood >= 10:
            log_fn(f"Successfully mined 10 wood! Total wood: {state.inventory.wood}")
            break
    
    return state