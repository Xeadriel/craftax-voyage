def drink_4_water(state, log_fn, step_func):
    # Water is in view (nearest 6 tiles), so I can directly drink 4 times
    state = drink(state, log_fn, step_func, number=4, max_steps=30)
    return state