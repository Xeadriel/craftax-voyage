def mine_2_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check I have a pickaxe that can mine coal (needs level >= 1)
    if state.inventory.pickaxe < 1:
        raise Exception("No pickaxe to mine coal")
    
    # Target: 2 more coal on top of what we have now (currently 0)
    target = state.inventory.coal + 2
    
    # First, explore until coal is in view
    state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
    
    # Mine 2 coal blocks (each gives 1 coal)
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 2, max_steps=40)
    
    return state