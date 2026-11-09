def mine_1_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, explore until a tree is in view
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=40)
    
    # Mine 1 tree (each tree gives exactly 1 wood)
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=30)
    
    return state