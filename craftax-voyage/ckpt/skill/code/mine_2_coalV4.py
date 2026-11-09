def mine_2_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check I have a pickaxe that can mine coal (needs level >= 1)
    if state.inventory.pickaxe < 1:
        raise Exception("No pickaxe to mine coal")
    
    # Target: 2 more coal on top of what we have now
    target = state.inventory.coal + 2
    
    # Mine coal one at a time, exploring for more between each
    for _ in range(2):
        if state.inventory.coal >= target:
            break
        
        # Explore until coal is in view
        state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
        
        # Mine 1 coal block
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1, max_steps=30)
    
    return state