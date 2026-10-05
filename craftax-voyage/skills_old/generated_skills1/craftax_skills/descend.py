# Skill: descend
# Purpose: Descends to the next floor using a ladder
# Required inputs: None (uses current position)
# Preconditions:
#   - Player must be on a floor with a closed ladder
#   - Player must have killed 8 monsters on current floor (except overworld)
#   - Player must be able to interact (not sleeping or resting)
# Expected effects:
#   - Player descends to next floor
#   - Ladder is opened on new floor
#   - Achievement may be triggered for descending
# Failure conditions:
#   - No ladder available
#   - Not enough monsters killed on current floor
#   - Player is on the last floor
# Explanation: Uses DESCEND action from constants.py and change_floor from game_logic.py
#           Checks monsters_killed from state to determine ladder availability
#           Ladder positions are stored in down_ladders from state

import jax.numpy as jnp
from craftax.craftax.constants import Action, MONSTERS_KILLED_TO_CLEAR_LEVEL
from craftax.craftax.craftax_state import EnvState


def descend(state: EnvState) -> EnvState:
    """
    Descends to the next floor using a ladder.
    
    Args:
        state: Current environment state
    
    Returns:
        New state with player on next floor
    
    Raises:
        ValueError: If descent is not possible
    """
    # Check if player is on the last floor
    if state.player_level >= 8:
        raise ValueError("Cannot descend from last floor")
    
    # Check if player has killed enough monsters
    if state.monsters_killed[state.player_level] < MONSTERS_KILLED_TO_CLEAR_LEVEL:
        raise ValueError(f"Need to kill {MONSTERS_KILLED_TO_CLEAR_LEVEL} monsters to open ladder")
    
    # Check if player is sleeping or resting
    if state.is_sleeping or state.is_resting:
        raise ValueError("Cannot descend while sleeping or resting")
    
    # Get ladder position
    ladder_position = state.up_ladders[state.player_level + 1]
    
    # Move to ladder position
    new_position = ladder_position
    new_direction = Action.UP.value  # Will be on up ladder
    
    # Mark ladder as opened on new floor
    new_chests_opened = state.chests_opened.at[state.player_level + 1].set(True)
    
    return state.replace(
        player_position=new_position,
        player_direction=new_direction,
        chests_opened=new_chests_opened,
        player_xp=state.player_xp + 1,
    )
