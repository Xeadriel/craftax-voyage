def mine_2_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, explore until a tree is in view
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=60)
    
    # Mine 2 trees (each gives exactly 1 wood)
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 2, max_steps=40)
    
    return state