# Description:
# Eats a ripe plant at the player's current position.
# Returns True if successfully ate the plant, False otherwise.
# Assumes a ripe plant is at the player's current position.

from craftax.craftax.constants import (
    Action,
    BlockType,
)


def eat_plant(env_step, state, max_steps=5):
    """
    Eats a ripe plant at the player's current position.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        max_steps: Maximum number of steps to attempt eating
    
    Returns:
        True if successfully ate plant, False otherwise
    """
    # Check if there's a ripe plant at the player's position
    block = state.map[state.player_level][state.player_position[0], state.player_position[1]]
    if block != BlockType.RIPE_PLANT.value:
        raise ValueError(f"Not a ripe plant at player position - found {BlockType(block).name}")
    
    # Check if player is hungry
    if state.player_food >= 7 + 2 * state.player_dexterity:
        raise ValueError("Player is not hungry")
    
    # Eat the plant
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while eating plant")
    
    return True
