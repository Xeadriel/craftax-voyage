def drink_6_water(state, log_fn, step_func):
    # First, explore until water is in view
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=50)
    
    # Then drink 6 times from water sources
    state = drink(state, log_fn, step_func, number=6, max_steps=40)
    
    return state