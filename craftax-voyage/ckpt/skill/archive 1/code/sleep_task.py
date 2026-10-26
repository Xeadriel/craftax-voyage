def sleep_task(state, log_fn, step_func):
    """
    Sleeps the player until energy is full.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the player slept until energy was full
        
    Raises:
        Exception: If the energy is already full, sleeping could not be started, the
            player was woken up early (e.g. by an attack), the player died (health
            dropped to 0), the player left the floor, or max_steps was reached before
            falling asleep
    """
    log_fn("Attempting to sleep...")
    log_fn(f"Current Energy: {state.player_energy}, Max Energy: {state.player_energy + state.player_strength}")
    
    # Use the sleep function which will automatically attempt to block in
    state = sleep(state, log_fn, step_func, max_steps=50)
    
    log_fn(f"Sleep complete! Final Energy: {state.player_energy}")
    
    return state