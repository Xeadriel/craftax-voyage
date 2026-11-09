def mine_4_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, explore until I can see a tree
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=40)
    
    # Then mine 4 trees (each tree gives exactly 1 wood)
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 4, max_steps=40)
    
    return state