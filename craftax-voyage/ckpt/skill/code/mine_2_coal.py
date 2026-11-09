def mine_2_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Target is 2 coal on top of what I have (0)
    target = state.inventory.coal + 2
    
    # I have a stone pickaxe (level 2), which can mine coal (requires level >= 1)
    
    # Explore until coal is in view
    state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
    
    # Mine coal until I have 2
    for _ in range(2):
        if state.inventory.coal >= target:
            break
        state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1, max_steps=30)
    
    return state