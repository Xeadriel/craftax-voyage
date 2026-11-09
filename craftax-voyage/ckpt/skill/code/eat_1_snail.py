def eat_1_snail(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # The snail is already in view (3 tiles away)
    # Kill the snail - it's a passive mob and will give +6 food when killed
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    return state