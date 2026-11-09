def kill_1_zombie(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # The zombie is already in view (2 tiles away)
    # Use kill_mob to hunt and kill the zombie
    state = kill_mob(state, log_fn, step_func, MobType.MELEE, max_steps=30)
    
    return state