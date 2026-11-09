def drink_6_water(state, log_fn, step_func):
    # Water is already in view (nearest 2 tiles), so I can directly drink 6 times
    state = drink(state, log_fn, step_func, number=6, max_steps=30)
    return state