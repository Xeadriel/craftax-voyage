def sleep_until_energy_full(state, log_fn, step_func):
    # Sleep until energy is full (max 50 steps for sleeping to start)
    state = sleep(state, log_fn, step_func, max_steps=50)
    return state