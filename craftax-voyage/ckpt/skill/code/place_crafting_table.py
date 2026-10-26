def place_crafting_table(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we already have a crafting table
    if state.inventory.wood >= 2:
        log_fn("Have enough wood to place crafting table")
    else:
        log_fn(f"Only have {state.inventory.wood} wood, need 2")
        # Need to collect more wood
        log_fn("Looking for a tree to mine")
        # Explore until we can see a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        # Mine the tree to get 1 wood
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    # Place the crafting table (it will automatically find a suitable position)
    log_fn("Placing crafting table")
    state = place(state, log_fn, step_func, "crafting_table")
    
    return state