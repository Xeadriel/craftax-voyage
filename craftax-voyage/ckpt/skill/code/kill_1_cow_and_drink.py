def kill_1_cow_and_drink(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType, MobType
    
    log_fn("Current food: " + str(state.player_food) + ", Current drink: " + str(state.player_drink))
    
    # Kill a passive mob (cow) - it's already visible at (-2, 4)
    log_fn("Looking for a cow to kill")
    state = kill_mob(state, log_fn, step_func, MobType.PASSIVE, max_steps=30)
    
    log_fn(f"Cow killed! Current food: {state.player_food}")
    
    # Now explore for water to drink
    log_fn("Looking for water to drink")
    state = explore_until(state, log_fn, step_func, BlockType.WATER, max_steps=100)
    
    # Drink from the water source
    log_fn("Drinking from water")
    state = drink(state, log_fn, step_func, number=3, max_steps=50)
    
    log_fn(f"Current drink: {int(state.player_drink)}")
    
    return state