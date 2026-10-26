def kill_1_cow(state, log_fn, step_func):
    """
    Kills 1 cow on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the cow was killed
    """
    log_fn("Starting to kill 1 cow")
    
    # The cow is already visible at (-4, 1), so we can kill it directly
    # MobType.PASSIVE with type_id 0 is a cow
    from craftax.craftax.constants import MobType
    
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0), max_steps=20)
    
    log_fn(f"Cow killed! Food increased from 3 to {state.inventory.food}")
    
    return state