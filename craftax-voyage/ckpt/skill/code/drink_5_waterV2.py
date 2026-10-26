def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    # Calculate how many more drinks we need
    current_drink = int(state.player_drink)
    drinks_needed = 5 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have enough water, task complete")
        return state
    
    # Drink from nearest water source
    log_fn(f"Drinking {drinks_needed} more times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state