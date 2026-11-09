def drink_3_water(state, log_fn, step_func):
    # A fountain is already in view (nearest 4 tiles)
    # Drink 3 times from the water source
    state = drink(state, log_fn, step_func, number=3, max_steps=30)
    return state