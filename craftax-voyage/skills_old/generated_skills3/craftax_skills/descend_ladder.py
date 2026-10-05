# Description:
# Descends to the next floor using a ladder.
# Returns True if successfully descended, False otherwise.
# Assumes a ladder is at the player's current position.

from craftax.craftax.constants import (
    Action,
    ItemType,
)


def descend_ladder(env_step, state, max_steps=5):
    """
    Descends to the next floor using a ladder.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        max_steps: Maximum number of steps to attempt descending
    
    Returns:
        True if successfully descended, False otherwise
    """
    # Check if player has a ladder
    if state.item_map[state.player_level][state.player_position[0], state.player_position[1]] != ItemType.LADDER_DOWN.value:
        raise ValueError("No ladder at player position")
    
    # Check if monsters have been killed on current level
    if state.monsters_killed[state.player_level] < 8:
        raise ValueError("Must kill 8 monsters on current level before descending")
    
    # Descend
    for _ in range(max_steps):
        state = env_step(None, state, Action.DESCEND.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while descending")
    
    return True
