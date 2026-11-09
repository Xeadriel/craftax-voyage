def place_1_furnace(state, log_fn, step_func):
    # I have 5 stone, need 1 for a furnace
    # Place the furnace on a free tile (the function will choose one)
    state = place(state, log_fn, step_func, "furnace")
    return state