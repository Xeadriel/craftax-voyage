def mine_3_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we already have 3 wood
    if state.inventory.wood >= 3:
        log_fn(f"Already have {state.inventory.wood} wood, task complete")
        return state
    
    # Mine trees until we have 3 wood
    trees_to_mine = 3 - state.inventory.wood
    
    for i in range(trees_to_mine):
        log_fn(f"Mining tree {i+1}/{trees_to_mine}")
        
        # Explore until we can see a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        # Mine the tree to get 1 wood
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Check if we have enough wood now
        if state.inventory.wood >= 3:
            log_fn(f"Reached target: {state.inventory.wood} wood")
            break
    
    return state