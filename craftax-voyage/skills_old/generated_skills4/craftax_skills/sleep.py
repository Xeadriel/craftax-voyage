# Description:
# Puts the player to sleep to recover health and energy.
# Returns True if successful, False if already sleeping or not enough energy.
# Handles sleep mechanics and wake-up conditions.

def sleep(state, max_steps=100):
    """
    Put the player to sleep.
    
    Args:
        state: Current environment state
        max_steps: Maximum steps to attempt (default 100)
    
    Returns:
        bool: True if sleeping, False otherwise
    """
    from craftax.craftax.constants import Action
    
    # Check if already sleeping
    if state.is_sleeping:
        raise ValueError("Already sleeping")
    
    # Check if we have enough energy to sleep
    if state.player_energy >= get_max_energy(state):
        raise ValueError("Already at maximum energy - cannot sleep")
    
    # Check if we're in a safe position (no mobs nearby)
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if is_in_mob(state, block_pos):
                    raise ValueError(f"Cannot sleep - mob at {block_pos}")
    
    # Put player to sleep
    state = state.replace(is_sleeping=True)
    
    return True
