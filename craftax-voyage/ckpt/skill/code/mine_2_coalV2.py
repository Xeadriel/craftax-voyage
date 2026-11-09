def mine_2_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Target is 2 coal on top of what I have (0)
    target = state.inventory.coal + 2
    
    # I have a stone pickaxe (level 2), which can mine coal (requires level >= 1)
    
    # Explore until coal is in view
    state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
    
    # Mine 2 coal blocks
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 2, max_steps=60)
    
    return state