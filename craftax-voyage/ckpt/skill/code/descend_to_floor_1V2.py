def descend_to_floor_1(state, log_fn, step_func):
    # The ladder down is open (36 tiles away), need sufficient steps to reach it
    # Use max_steps=60 to allow navigation through obstacles and reaching the ladder
    state = descend_ladder(state, log_fn, step_func, max_steps=60)
    return state