def place_1_furnace(state, log_fn, step_func):
    # Check I have enough stone (need 1 for a furnace)
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to place a furnace (need 1, have {})".format(state.inventory.stone))
    
    # Place the furnace on a free tile (the function will choose one automatically)
    state = place(state, log_fn, step_func, "furnace", max_steps=20)
    
    return state