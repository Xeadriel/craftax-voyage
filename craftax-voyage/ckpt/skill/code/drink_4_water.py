def drink_4_water(state, log_fn, step_func):
    # I have water in view (nearest 4 tiles), so I can directly drink
    state = drink(state, log_fn, step_func, number=4, max_steps=30)
    return state