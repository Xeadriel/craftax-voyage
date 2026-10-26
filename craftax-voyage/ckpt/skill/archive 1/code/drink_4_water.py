def drink_4_water(state, log_fn, step_func):
    """
    Drinks 4 water from the nearest water source in sight.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after drinking 4 water
    """
    log_fn("Starting to drink 4 water...")
    state = drink(state, log_fn, step_func, number=4, max_steps=20)
    log_fn(f"Successfully drank 4 water! Current drink: {state.player_drink}")
    return state