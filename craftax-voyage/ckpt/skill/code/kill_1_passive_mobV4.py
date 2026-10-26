def kill_1_passive_mob(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType, MobType
    
    log_fn("Looking for a passive mob to kill")
    
    # Check if I already have a sword
    if state.inventory.sword > 0:
        log_fn(f"Have a {['none', 'wood', 'stone', 'iron', 'diamond'][min(state.inventory.sword, 4)]} sword")
    else:
        log_fn("No sword, need to craft a wood sword first")
        
        # Need 3 wood total: 2 for crafting table + 1 for wood sword
        total_wood_needed = 3
        current_wood = state.inventory.wood
        
        log_fn(f"Need {total_wood_needed} wood, have {current_wood}")
        
        # Mine trees to get enough wood
        if current_wood < total_wood_needed:
            trees_to_mine = total_wood_needed - current_wood
            log_fn(f"Need to mine {trees_to_mine} more tree(s)")
            
            for i in range(trees_to_mine):
                log_fn(f"Mining tree {i+1}/{trees_to_mine}")
                state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=30)
                state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=10)
            
            log_fn(f"Have {state.inventory.wood} wood")
        
        # Place crafting table
        log_fn("Placing crafting table")
        state = place(state, log_fn, step_func, "crafting_table", max_steps=20)
        
        # Craft wood sword
        log_fn("Crafting wood sword")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD, number=1, max_steps=20)
    
    # Check survival - if critically low, restore before hunting
    if state.player_health <= 2 or state.player_food <= 2 or state.player_drink <= 2 or state.player_energy <= 2:
        log_fn("Survival stats low! Need to restore before hunting")
        # Drink if needed
        if state.player_drink <= 2:
            log_fn("Looking for water to drink")
            state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=50)
            if state.player_drink <= 2:
                state = drink(state, log_fn, step_func, number=2, max_steps=50)
        
        # Sleep if energy is very low
        if state.player_energy <= 2:
            log_fn("Energy low, attempting to sleep")
            state = sleep(state, log_fn, step_func, max_steps=50)
    
    # Now explore to find a passive mob
    log_fn("Exploring to find a passive mob")
    state = explore_until(state, log_fn, step_func, MobType.PASSIVE, max_steps=80)
    
    # Kill the passive mob
    log_fn("Killing a passive mob")
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    log_fn(f"Successfully killed a passive mob. Current food: {state.player_food}")
    
    return state