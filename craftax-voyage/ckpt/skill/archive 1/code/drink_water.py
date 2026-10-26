def drink_water(state, log_fn, step_func):
    """
    Drinks 1 water from the nearest water source in sight.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after drinking 1 water
    """
    log_fn("Drinking 1 water...")
    state = drink(state, log_fn, step_func, number=1, max_steps=20)
    return state