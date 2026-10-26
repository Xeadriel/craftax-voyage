def drink_4_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Exploring for water source...")
    
    # Explore until we find water
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    log_fn("Found water source!")
    
    # Drink 4 times from the water
    state = drink(state, log_fn, step_func, number=4, max_steps=20)
    log_fn(f"Successfully drank 4 water! Current drink: {state.player_drink}")
    
    return state