# Description:
# Sleeps at the player's current position to recover energy and health.
# Returns True if successfully slept, False otherwise.
# Assumes the player has enough energy to sleep.

from craftax.craftax.constants import (
    Action,
)


def sleep(env_step, state, max_steps=5):
    """
    Sleeps at the player's current position.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        max_steps: Maximum number of steps to attempt sleeping
    
    Returns:
        True if successfully slept, False otherwise
    """
    # Check if player has enough energy
    if state.player_energy >= 7 + 2 * state.player_dexterity:
        raise ValueError("Player has enough energy, cannot sleep")
    
    # Sleep
    for _ in range(max_steps):
        state = env_step(None, state, Action.SLEEP.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while sleeping")
    
    return True
