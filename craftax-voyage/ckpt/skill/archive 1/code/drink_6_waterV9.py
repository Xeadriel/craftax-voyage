def drink_6_water(state, log_fn, step_func):
    """
    Drinks 6 water from the nearest water source on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after drinking 6 water
    """
    log_fn("Starting to drink 6 water")
    log_fn(f"Current drink level: {state.player_drink}")
    
    # Use the drink function which will automatically find and drink from water
    # The function has built-in logic to find the nearest water source
    state = drink(state, log_fn, step_func, number=6, max_steps=20)
    
    log_fn(f"Successfully drank 6 water! Final drink count: {state.player_drink}")
    log_fn(f"Health after drinking: {state.player_health}")
    
    return state