def mine_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Looking for a tree...")
    state = explore_until(state, log_fn, step_func, BlockType.TREE)
    log_fn("Found a tree!")
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    return state