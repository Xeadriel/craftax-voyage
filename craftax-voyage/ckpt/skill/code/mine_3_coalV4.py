def mine_3_coal(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Mining 3 coal")
    
    # Check if we already have 3 coal
    if state.inventory.coal >= 3:
        log_fn(f"Already have {state.inventory.coal} coal, task complete")
        return state
    
    # Check if we have a pickaxe
    if state.inventory.pickaxe < 1:
        log_fn("Need a pickaxe to mine coal")
        
        # We need 1 wood for wood pickaxe
        wood_needed = 1
        
        # Check if we have enough wood
        if state.inventory.wood < wood_needed:
            log_fn(f"Need {wood_needed} wood for pickaxe, have {state.inventory.wood}")
            
            # Mine trees to get enough wood
            trees_to_mine = wood_needed - state.inventory.wood
            log_fn(f"Need to mine {trees_to_mine} more tree(s)")
            
            for i in range(trees_to_mine):
                log_fn(f"Mining tree {i+1}/{trees_to_mine}")
                state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=30)
                state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=10)
            
            # Check if we have enough wood now
            if state.inventory.wood < wood_needed:
                log_fn(f"Still need wood, have {state.inventory.wood}")
        
        # Craft wood pickaxe
        log_fn("Crafting wood pickaxe")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE, number=1, max_steps=20)
        
        # Verify we have a pickaxe now
        if state.inventory.pickaxe < 1:
            log_fn("Failed to craft pickaxe")
            raise Exception("Failed to craft wood pickaxe")
    
    # Calculate how many more coal we need
    coal_needed = 3 - state.inventory.coal
    
    log_fn(f"Need to mine {coal_needed} more coal blocks, currently have {state.inventory.coal}")
    
    # Mine coal blocks until we have 3
    for i in range(coal_needed):
        log_fn(f"Mining coal {i+1}/{coal_needed}")
        
        # Explore until we can see a coal block
        log_fn("Exploring to find coal...")
        state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=100)
        
        # Mine the coal block
        log_fn("Mining coal block")
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1, max_steps=30)
        
        # Check if we have enough coal now
        if state.inventory.coal >= 3:
            log_fn(f"Reached target: {state.inventory.coal} coal")
            break
    
    log_fn(f"Successfully mined 3 coal. Current inventory: {state.inventory.coal} coal")
    
    return state