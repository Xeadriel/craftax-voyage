def obtain_1_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Obtaining 1 wood")
    
    # Check if we already have wood
    if state.inventory.wood >= 1:
        log_fn(f"Already have {state.inventory.wood} wood, task complete")
        return state
    
    # Use the obtain_wood function to mine 1 wood
    state = obtain_wood(state, log_fn, step_func)
    
    log_fn(f"Obtained wood. Current inventory: {state.inventory.wood} wood")
    
    return state