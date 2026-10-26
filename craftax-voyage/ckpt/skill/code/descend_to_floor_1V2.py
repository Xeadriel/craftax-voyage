def descend_to_floor_1(state, log_fn, step_func):
    from craftax.craftax.constants import ItemType, Action
    
    log_fn("Attempting to descend to floor 1")
    
    # Check survival stats - if critically low, prioritize survival
    if state.player_food <= 2 or state.player_drink <= 2 or state.player_energy <= 2:
        log_fn("Survival stats critically low! Need to restore before descending")
        
        # Drink water if needed
        if state.player_drink <= 2:
            log_fn("Looking for water to drink")
            state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN, max_steps=50)
            if state.player_drink <= 2:
                state = drink(state, log_fn, step_func, number=2, max_steps=50)
        
        # Sleep if energy is very low
        if state.player_energy <= 2:
            log_fn("Energy critically low, attempting to sleep")
            state = sleep(state, log_fn, step_func, max_steps=50)
    
    # Explore until we can see the ladder down
    log_fn("Exploring to find the ladder down")
    state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN, max_steps=100)
    
    log_fn("Found the ladder down, now descending")
    
    # Descend the ladder
    state = descend_ladder(state, log_fn, step_func, max_steps=20)
    
    log_fn("Successfully descended to floor 1")
    
    return state