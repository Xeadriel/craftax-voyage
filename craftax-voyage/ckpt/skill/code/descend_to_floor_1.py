def descend_to_floor_1(state, log_fn, step_func):
    # The ladder down is open on floor 0, so we can descend directly
    state = descend_ladder(state, log_fn, step_func, max_steps=20)
    return state