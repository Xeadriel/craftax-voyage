def kill_1_passive_mob(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    log_fn("Looking for a passive mob to kill")
    
    # Explore until we can see a passive mob (increased max_steps from 20 to 50)
    state = explore_until(state, log_fn, step_func, MobType.PASSIVE, max_steps=50)
    
    # Kill the passive mob
    log_fn("Killing a passive mob")
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=20)
    
    log_fn(f"Successfully killed a passive mob. Current food: {state.player_food}")
    
    return state