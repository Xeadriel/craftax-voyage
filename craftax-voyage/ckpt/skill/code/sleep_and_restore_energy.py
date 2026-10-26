def sleep_and_restore_energy(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    log_fn("Checking if we can sleep to restore energy")
    
    # Check if energy is already full (max is 9)
    if state.player_energy >= 9:
        log_fn("Energy is already full, no need to sleep")
        return state
    
    # Check prerequisites: need food, drink, and energy above 0
    if state.player_food <= 0 or state.player_drink <= 0 or state.player_energy <= 0:
        log_fn("Cannot sleep: need food, drink and energy above 0")
        raise Exception("Cannot sleep: need food, drink and energy above 0")
    
    log_fn(f"Current energy: {state.player_energy}/9")
    log_fn(f"Current food: {state.player_food}/9, Drink: {state.player_drink}/9")
    
    # Call the built-in sleep function which handles walling in and sleeping
    # max_steps=50 is sufficient for sleeping to complete (regenerates 1 energy per 11 steps)
    state = sleep(state, log_fn, step_func, max_steps=50)
    
    log_fn(f"Sleep complete. Current energy: {state.player_energy}/9")
    
    return state