def place_furnace(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Placing a furnace")
    
    # Check if we have enough stone (need 1)
    if state.inventory.stone < 1:
        log_fn(f"Need 1 stone, but have {state.inventory.stone}")
        raise Exception(f"Not enough stone to place furnace. Need 1, have {state.inventory.stone}")
    
    # Place the furnace
    state = place(state, log_fn, step_func, "furnace")
    
    log_fn("Furnace placed successfully")
    
    return state