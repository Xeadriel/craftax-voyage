from craftax.craftax.constants import MobType

def kill_one_cow(state, log_fn, step_func):
    """
    Kills 1 cow in sight on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after the cow was killed
    
    Raises:
        Exception: If no cow is in sight or if the player dies
    """
    log_fn("Looking for a cow...")
    
    # Explore until we find a cow
    state = explore_until(state, log_fn, step_func, (MobType.PASSIVE, 0))
    log_fn("Found a cow!")
    
    # Kill the cow - this will give +6 food
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0))
    log_fn(f"Successfully killed the cow! Current food: {state.inventory.food}")
    
    return state