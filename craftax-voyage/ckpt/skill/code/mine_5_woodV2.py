def mine_5_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Target: 5 more wood on top of what we have now
    target = state.inventory.wood + 5
    
    # Mine trees one at a time, exploring for more between each
    for _ in range(5):
        if state.inventory.wood >= target:
            break
        
        # Explore until a tree is in view
        state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=60)
        
        # Mine 1 tree (gives 1 wood)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=30)
    
    return state