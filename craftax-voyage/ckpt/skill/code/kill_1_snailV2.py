def kill_1_snail(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # The Snail is already in view (3 tiles away)
    # Use kill_mob to hunt and kill the Snail (it's a passive mob)
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    return state