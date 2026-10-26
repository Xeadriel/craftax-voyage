def drink_6_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    # Calculate how many more drinks we need (6 total)
    current_drink = int(state.player_drink)
    drinks_needed = 6 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have enough water, task complete")
        return state
    
    # Ensure water is in sight before drinking
    log_fn("Looking for water to drink")
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    
    # Drink from the nearest water source
    log_fn(f"Drinking {drinks_needed} more times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state