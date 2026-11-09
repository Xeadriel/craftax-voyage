def drink_5_water(state, log_fn, step_func):
    # Water is already in view (nearest 2 tiles), so I can directly drink 5 times
    state = drink(state, log_fn, step_func, number=5, max_steps=30)
    return state