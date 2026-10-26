def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn(f"Current drink: {int(state.player_drink)}, need 5 total")
    
    # Calculate how many more drinks we need
    current_drink = int(state.player_drink)
    drinks_needed = 5 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have 5 or more drinks, task complete")
        return state
    
    # Water is visible on the map, so we need to explore first to find it
    log_fn(f"Exploring to find water fountain or source, need {drinks_needed} drinks")
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
    
    # Once we have water in sight, drink from it
    log_fn(f"Found water source, drinking {drinks_needed} times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state