# Description:
# Levels up a specified attribute using experience points.
# Returns True if successfully leveled up, False otherwise.
# Assumes the player has enough XP to level up.

from craftax.craftax.constants import (
    Action,
)


def level_up_attribute(env_step, state, attribute_name, max_steps=5):
    """
    Levels up a specified attribute.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        attribute_name: "dexterity", "strength", or "intelligence"
        max_steps: Maximum number of steps to attempt leveling up
    
    Returns:
        True if successfully leveled up, False otherwise
    """
    # Check if player has enough XP
    if state.player_xp < 1:
        raise ValueError("Player has no experience points to level up")
    
    # Check if attribute can be leveled up
    if attribute_name == "dexterity" and state.player_dexterity >= 5:
        raise ValueError("Dexterity is already at maximum level")
    if attribute_name == "strength" and state.player_strength >= 5:
        raise ValueError("Strength is already at maximum level")
    if attribute_name == "intelligence" and state.player_intelligence >= 5:
        raise ValueError("Intelligence is already at maximum level")
    
    # Level up the attribute
    for _ in range(max_steps):
        if attribute_name == "dexterity":
            state = env_step(None, state, Action.LEVEL_UP_DEXTERITY.value, None)
        elif attribute_name == "strength":
            state = env_step(None, state, Action.LEVEL_UP_STRENGTH.value, None)
        elif attribute_name == "intelligence":
            state = env_step(None, state, Action.LEVEL_UP_INTELLIGENCE.value, None)
        
        if state.player_health <= 0:
            raise ValueError("Player died while leveling up attribute")
    
    return True
