def drink_3_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Drinking 3 water")
    
    # Always drink 3 times to complete the task
    state = drink(state, log_fn, step_func, number=3, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state