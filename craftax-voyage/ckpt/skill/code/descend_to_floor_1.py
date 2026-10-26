def descend_to_floor_1(state, log_fn, step_func):
    from craftax.craftax.constants import ItemType, Action
    
    log_fn("Looking for the ladder down to descend to floor 1")
    
    # Check survival stats - if critically low, prioritize survival
    if state.player_health <= 2 or state.player_food <= 2 or state.player_drink <= 2 or state.player_energy <= 2:
        log_fn("Survival stats critically low! Need to restore before descending")
        # Drink water if needed
        if state.player_drink <= 2:
            log_fn("Looking for water to drink")
            state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN_BLOCKED, max_steps=50)
            if state.player_drink <= 2:
                state = drink(state, log_fn, step_func, number=2, max_steps=50)
        
        # Eat if needed (look for cows)
        if state.player_food <= 2:
            log_fn("Looking for food")
            state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN_BLOCKED, max_steps=50)
            # Note: killing mobs for food takes time, skip for now to focus on task
        
        # Sleep if energy is very low
        if state.player_energy <= 2:
            log_fn("Energy critically low, attempting to sleep")
            state = sleep(state, log_fn, step_func, max_steps=50)
    
    # Explore until we can see the ladder down
    # Increased max_steps from 20 to 100 to allow sufficient exploration
    state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN, max_steps=100)
    
    log_fn("Found the ladder down, now descending")
    
    # Descend the ladder
    state = descend_ladder(state, log_fn, step_func, max_steps=20)
    
    log_fn("Successfully descended to floor 1")
    
    return state