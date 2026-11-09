def place_4_stone(state, log_fn, step_func):
    # Place 4 stone blocks
    # I have 7 stone, need to place 4 more
    for _ in range(4):
        state = place(state, log_fn, step_func, "stone")
    
    return state