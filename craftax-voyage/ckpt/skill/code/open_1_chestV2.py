def open_1_chest(state, log_fn, step_func):
    # The chest is already in view (nearest 2 tiles), so we can directly open it
    state = open_chest(state, log_fn, step_func, number=1, max_steps=30)
    return state