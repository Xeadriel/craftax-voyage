def kill_1_cow(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # Explore until a passive mob (cow) is in view
    state = explore_until(state, log_fn, step_func, MobType.PASSIVE, max_steps=60)
    
    # Kill the cow - it's a passive mob and will give +6 food when killed
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    return state