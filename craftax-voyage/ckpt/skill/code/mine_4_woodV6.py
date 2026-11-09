def mine_4_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, explore until at least one tree is in view
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=40)
    
    # Mine 4 trees in smaller batches to ensure all are found
    # Each tree gives exactly 1 wood
    for _ in range(4):
        # Explore to find more trees if needed
        state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=30)
        
        # Mine 1 tree at a time
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=20)
    
    return state