def mine_1_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Ensure we can see a tree first
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=20)
    
    # Mine 1 wood from the tree (each tree gives exactly 1 wood)
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=20)
    
    return state