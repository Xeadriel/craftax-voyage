def kill_1_zombie(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType, MobType
    
    # Check if I already have a sword
    if state.inventory.sword > 0:
        log_fn(f"Already have a {['none', 'wood', 'stone', 'iron', 'diamond'][min(state.inventory.sword, 4)]} sword")
    else:
        log_fn("No sword, need to craft a wood sword")
        
        # Need 3 wood total: 2 for crafting table, 1 for wood sword
        wood_needed = 3
        current_wood = state.inventory.wood
        
        log_fn(f"Need {wood_needed} wood, have {current_wood}")
        
        # Mine trees to get enough wood
        if current_wood < wood_needed:
            trees_to_mine = wood_needed - current_wood
            log_fn(f"Need to mine {trees_to_mine} more trees")
            
            for i in range(trees_to_mine):
                log_fn(f"Mining tree {i+1}/{trees_to_mine}")
                state = explore_until(state, log_fn, step_func, BlockType.TREE)
                state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
            
            # Check if we have enough wood now
            if state.inventory.wood < wood_needed:
                log_fn(f"Still need wood, have {state.inventory.wood}")
        
        # Place crafting table
        log_fn("Placing crafting table")
        state = place(state, log_fn, step_func, "crafting_table")
        
        # Craft wood sword
        log_fn("Crafting wood sword")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
    
    # Now kill the zombie
    log_fn("Looking for a zombie to kill")
    state = explore_until(state, log_fn, step_func, MobType.MELEE)
    
    log_fn("Killing zombie")
    state = kill_mob(state, log_fn, step_func, MobType.MELEE)
    
    log_fn(f"Successfully killed a zombie. Current food: {state.player_food}")
    
    return state