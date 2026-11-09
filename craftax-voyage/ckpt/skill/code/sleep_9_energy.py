def sleep_9_energy(state, log_fn, step_func):
    # Sleep until energy is full
    state = sleep(state, log_fn, step_func, max_steps=50)
    return state