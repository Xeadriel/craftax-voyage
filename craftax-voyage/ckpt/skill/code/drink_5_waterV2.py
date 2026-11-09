def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Water is seen on this floor at 20 tiles but not in view
    # First, explore until water is in view
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=60)
    
    # Then drink 5 times from the water source
    state = drink(state, log_fn, step_func, number=5, max_steps=30)
    
    return state