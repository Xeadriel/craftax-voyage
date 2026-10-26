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
    
    # Water is visible on the map, so we don't need to explore first
    # Use the drink function to drink from the nearest water source
    log_fn(f"Drinking {drinks_needed} times from nearest water source")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state