def kill_1_cow(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    log_fn("Looking for a cow to kill")
    
    # Kill the cow (PASSIVE mob type)
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE)
    
    log_fn("Cow killed successfully")
    
    return state