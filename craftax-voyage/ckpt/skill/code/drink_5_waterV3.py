def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType, ItemType
    
    log_fn(f"Current drink: {int(state.player_drink)}, need 5 total")
    
    # Calculate how many more drinks we need
    current_drink = int(state.player_drink)
    drinks_needed = 5 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have enough water, task complete")
        return state
    
    # Check survival - health is critical at 1.0
    if state.player_health <= 2:
        log_fn("Health is critically low! Need to restore before drinking")
        # Need food, drink, and energy to sleep
        if state.player_food <= 2:
            log_fn("Looking for food")
            # Kill a mob for food
            state = explore_until(state, log_fn, step_func, ItemType.LADDER_DOWN_BLOCKED, max_steps=30)
            state = kill_mob(state, log_fn, step_func, ItemType.LADDER_DOWN_BLOCKED, max_steps=30)
        
        # We need drink too, but that's the task - let's try to explore first
        # Sleep requires energy > 0, so we need to survive first
    
    # Explore until we can see a water source (fountain or water)
    # Increased max_steps from 50 to 100 to allow sufficient exploration
    log_fn(f"Exploring to find water fountain or source, need {drinks_needed} drinks")
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
    
    # If we still don't have water visible, try to find a fountain
    # Fountains are on Floor 1 in about half the rooms
    if state.player_drink <= current_drink:  # Check if we still need drinks
        log_fn("Water not found yet, looking for fountain")
        state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
    
    # Once we have water in sight, drink from it
    log_fn(f"Found water source, drinking {drinks_needed} times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state

def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn(f"Current drink: {int(state.player_drink)}, need 5 total")
    
    # Calculate how many more drinks we need
    current_drink = int(state.player_drink)
    drinks_needed = 5 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have enough water, task complete")
        return state
    
    # Explore until we can see a water source (fountain or water)
    # Increased max_steps to 100 to allow sufficient exploration
    log_fn(f"Exploring to find water fountain or source, need {drinks_needed} drinks")
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
    
    # Once we have water in sight, drink from it
    log_fn(f"Found water source, drinking {drinks_needed} times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state

def drink_5_water(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn(f"Current drink: {int(state.player_drink)}, need 5 total")
    
    # Calculate how many more drinks we need
    current_drink = int(state.player_drink)
    drinks_needed = 5 - current_drink
    
    log_fn(f"Need {drinks_needed} more drinks, currently have {current_drink}")
    
    if drinks_needed <= 0:
        log_fn("Already have enough water, task complete")
        return state
    
    # Explore until we can see a water source (fountain or water)
    # Increased max_steps significantly to allow thorough exploration of Floor 1 rooms
    log_fn(f"Exploring to find water fountain or source, need {drinks_needed} drinks")
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=150)
    
    # Once we have water in sight, drink from it
    log_fn(f"Found water source, drinking {drinks_needed} times")
    state = drink(state, log_fn, step_func, number=drinks_needed, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state