def rest(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check if health is below maximum (max is 9 at attribute level 1)
    # Maximum health = 9 + (strength - 1) = 9 + 0 = 9 at strength level 1
    max_health = 9 + (state.player_strength - 1)
    
    log_fn(f"Current health: {state.player_health}, Maximum health: {max_health}")
    
    if state.player_health >= max_health:
        log_fn("Health is already at maximum, no need to rest")
        return state
    
    log_fn("Health is below maximum, attempting to REST")
    
    # Use REST action (value 17)
    state = step_func(Action.REST.value)
    
    log_fn(f"REST started. Current health: {state.player_health}")
    
    return state