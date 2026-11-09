def mine_2_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType, Action
    
    # Calculate target: need 2 more coal on top of what we have (1 -> 3)
    target = state.inventory.coal + 2
    
    # I have a stone pickaxe (level 2) which can mine coal (requires level >= 1)
    
    # Mine coal one at a time, exploring for more between each mining
    for _ in range(2):
        # Explore until coal is in view with a larger budget (coal is at ~28 tiles)
        state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=120)
        
        # Mine 1 coal block
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1, max_steps=40)
        
        # Check if we've reached the target
        if state.inventory.coal >= target:
            break
    
    return state