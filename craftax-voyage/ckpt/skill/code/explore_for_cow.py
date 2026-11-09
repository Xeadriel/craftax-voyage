def explore_for_cow(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # Explore until a passive mob (cow) is in view
    state = explore_until(state, log_fn, step_func, MobType.PASSIVE, max_steps=60)
    
    return state