def drink_8_water(state, log_fn, step_func):
    # Water is already in view (nearest 4 tiles), so I can directly drink
    state = drink(state, log_fn, step_func, number=8, max_steps=30)
    return state