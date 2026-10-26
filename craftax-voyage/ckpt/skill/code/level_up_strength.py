def level_up_strength(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    log_fn(f"Current XP: {state.player_xp}, Current Strength: {state.player_strength}")
    
    # Check if we have enough XP to level up (need at least 1 XP)
    if state.player_xp < 1:
        log_fn("Not enough XP to level up Strength")
        raise Exception("Not enough XP to level up Strength")
    
    # Check if we're already at max strength level (5)
    if state.player_strength >= 5:
        log_fn(f"Already at max Strength level {state.player_strength}")
        return state
    
    log_fn("Leveling up Strength...")
    
    # Use the LEVEL_UP_STRENGTH action to spend 1 XP
    # step_func takes state (already available as parameter) and action value
    state = step_func(Action.LEVEL_UP_STRENGTH.value)
    
    log_fn(f"Strength leveled up! New Strength: {state.player_strength}")
    
    return state