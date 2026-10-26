def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Drinking 5 water")
    
    # Convert player_drink from JAX array to Python int
    current_drink = int(state.player_drink)
    
    # Calculate how many more drinks we need
    drinks_needed = 5 - current_drink
    
    if drinks_needed <= 0:
        log_fn(f"Already have {current_drink} drinks, task complete")
        return state
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    # Drink from nearest water source
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state