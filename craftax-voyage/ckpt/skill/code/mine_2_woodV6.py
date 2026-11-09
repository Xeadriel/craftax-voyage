def mine_2_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Target: 2 more wood on top of what we have now
    target = state.inventory.wood + 2
    
    # Mine trees one at a time, exploring for more between each
    while state.inventory.wood < target:
        # Explore until a tree is in view
        state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=60)
        
        # Mine 1 tree (gives 1 wood)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=30)
    
    return state