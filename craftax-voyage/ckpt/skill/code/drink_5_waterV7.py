def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Drinking 5 water")
    
    # Call the built-in drink function to drink 5 times from the nearest water source
    state = drink(state, log_fn, step_func, number=5, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state