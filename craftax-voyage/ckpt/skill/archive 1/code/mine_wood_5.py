def mine_wood_5(state, log_fn, step_func):
    log_fn("Starting to mine 5 wood")
    
    # Check current wood inventory
    if state.inventory.wood >= 5:
        log_fn("Already have 5 wood!")
        return state
    
    # Need to mine (5 - current) more trees
    trees_to_mine = 5 - state.inventory.wood
    log_fn(f"Need to mine {trees_to_mine} more trees")
    
    # Explore until we find a tree
    state = explore_until(state, log_fn, step_func, BlockType.TREE)
    log_fn("Found a tree!")
    
    # Mine the tree
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    log_fn("Mined tree!")
    
    # Continue mining until we have 5 wood
    for _ in range(trees_to_mine - 1):
        if state.inventory.wood >= 5:
            break
        # Explore to find another tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn(f"Successfully mined 5 wood! Current wood: {state.inventory.wood}")
    return state