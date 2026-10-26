def drink_6_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Task: Drink 6 water (gain 6 additional drinks)")
    
    # Check if we already have 6 drinks
    current_drink = int(state.player_drink)
    
    if current_drink >= 6:
        log_fn(f"Already have {current_drink} drinks, task complete")
        return state
    
    # Calculate how many more drinks we need
    drinks_needed = 6 - current_drink
    log_fn(f"Need to drink {drinks_needed} more times")
    
    # Check if water is visible using known_blocks (which returns the full map)
    known = known_blocks(state)
    visible = visible_mask(state)
    
    water_found = False
    for row in range(-4, 5):
        for col in range(-5, 6):
            if is_visible(state, row, col) and known[row, col] == BlockType.WATER:
                water_found = True
                break
        if water_found:
            break
    
    if not water_found:
        log_fn("Water not visible, exploring to find water")
        state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
        # Check again after exploring
        known = known_blocks(state)
        visible = visible_mask(state)
        for row in range(-4, 5):
            for col in range(-5, 6):
                if is_visible(state, row, col) and known[row, col] == BlockType.WATER:
                    water_found = True
                    break
            if water_found:
                break
    
    if not water_found:
        log_fn("Water still not found, cannot complete task")
        raise Exception("Water not found")
    
    # Once we have water in sight, drink from it
    log_fn(f"Found water, drinking {drinks_needed} times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state