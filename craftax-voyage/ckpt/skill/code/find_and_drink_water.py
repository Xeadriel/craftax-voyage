def find_and_drink_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Looking for water to drink")
    
    # Explore until we can see a water source (water or fountain)
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    
    # Now drink from the water source
    log_fn("Drinking from water")
    state = drink(state, log_fn, step_func, number=1)
    
    log_fn(f"Current drink: {state.player_drink}")
    
    return state