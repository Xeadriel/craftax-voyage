def drink_8_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, explore until water is in view
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=60)
    
    # Then drink 8 times from the water source
    state = drink(state, log_fn, step_func, number=8, max_steps=60)
    
    return state