def eat_1_cow(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # The cow is already in view (nearest 2 tiles)
    # Use kill_mob to hunt and kill the cow
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    return state