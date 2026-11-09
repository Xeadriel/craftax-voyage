def kill_1_zombie(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # Use kill_mob to hunt and kill a zombie (melee mob)
    # The function will automatically find and kill a matching mob in view
    state = kill_mob(state, log_fn, step_func, MobType.MELEE, max_steps=40)
    
    return state