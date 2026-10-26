def obtain_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Looking for a tree to mine")
    
    # Explore until we can see a tree
    state = explore_until(state, log_fn, step_func, BlockType.TREE)
    
    # Mine the tree to get 1 wood
    log_fn("Mining a tree")
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn(f"Obtained wood. Current inventory: {state.inventory.wood} wood")
    
    return state