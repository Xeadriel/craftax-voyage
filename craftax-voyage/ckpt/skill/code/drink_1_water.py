def drink_1_water(state, log_fn, step_func):
    # First, explore until water is in view
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=50)
    
    # Then drink 1 time from the water source
    state = drink(state, log_fn, step_func, number=1, max_steps=20)
    
    return state