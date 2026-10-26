from craftax.craftax.constants import MobType

def kill_1_skeleton(state, log_fn, step_func):
    """
    Kills 1 skeleton on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the skeleton was killed
    """
    log_fn("Starting to kill 1 skeleton")
    
    # The skeleton is already visible on the map at (-5, 0)
    # Use kill_mob which handles positioning and attacking automatically
    log_fn("Killing skeleton...")
    
    # Skeletons are ranged mobs with type_id 0
    state = kill_mob(state, log_fn, step_func, (MobType.RANGED, 0), max_steps=20)
    
    log_fn("Skeleton killed successfully!")
    
    return state