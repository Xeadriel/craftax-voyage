from craftax.craftax.constants import Action, BlockType

def sleep_safe(state, log_fn, step_func):
    """
    Safely sleeps the player by blocking in with stone on all 4 sides,
    then sleeping until energy is full.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the player slept until energy was full
    """
    log_fn("Attempting to sleep safely")
    log_fn(f"Current Energy: {state.player_energy}, Max Energy: {state.player_recover}")
    
    # Check if energy is full - if so, there's no need to sleep
    if state.player_energy >= state.player_recover:
        log_fn("Energy is already full, no need to sleep")
        return state
    
    # Check if we have enough stone to block in (need 4 stone blocks)
    if state.inventory.stone < 4:
        log_fn(f"Not enough stone to block in (need 4, have {state.inventory.stone})")
        
        # Need to mine more stone first
        log_fn("Mining 4 more stone blocks to block in")
        
        # Mine stone until we have 4 more
        for i in range(4):
            log_fn(f"Stone {i+1}/4 - exploring for stone...")
            state = explore_until(state, log_fn, step_func, BlockType.STONE)
            log_fn(f"Stone {i+1}/4 - found in sight!")
            
            log_fn(f"Stone {i+1}/4 - mining...")
            state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
            
            log_fn(f"Stone {i+1}/4 - mined. Stone remaining: {state.inventory.stone}")
        
        log_fn(f"Mined 4 stone blocks. Total stone: {state.inventory.stone}")
    
    # Now use the sleep function which handles blocking in automatically
    log_fn("Sleeping until energy is full...")
    state = sleep(state, log_fn, step_func, max_steps=50)
    
    log_fn(f"Sleep complete! Final Energy: {state.player_energy}")
    
    return state