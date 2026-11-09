def drink_2_water(state, log_fn, step_func):
    # Water is already in view (nearest 2 tiles), so I can directly drink
    state = drink(state, log_fn, step_func, number=2, max_steps=20)
    return state