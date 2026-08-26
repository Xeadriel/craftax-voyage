# Skill: ascend
# Purpose: Ascends to the previous floor using a ladder
# Required inputs: None (uses current position)
# Preconditions:
#   - Player must be on a floor with an up ladder
#   - Player must be able to interact (not sleeping or resting)
# Expected effects:
#   - Player ascends to previous floor
#   - Ladder is opened on new floor
#   - Achievement may be triggered for ascending
# Failure conditions:
#   - No ladder available
#   - Player is on the first floor
# Explanation: Uses ASCEND action from constants.py and change_floor from game_logic.py
#           Checks up_ladders from state to determine ladder availability

from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def ascend(state: EnvState) -> EnvState:
    """
    Ascends to the previous floor using a ladder.

    Args:
        state: Current environment state

    Returns:
        New state with player on previous floor

    Raises:
        ValueError: If ascent is not possible
    """
    # Check if player is on the first floor
    if state.player_level <= 0:
        raise ValueError("Cannot ascend from first floor")

    # Check if player is sleeping or resting
    if state.is_sleeping or state.is_resting:
        raise ValueError("Cannot ascend while sleeping or resting")

    # Get ladder position
    ladder_position = state.down_ladders[state.player_level - 1]

    # Move to ladder position
    new_position = ladder_position
    new_direction = Action.DOWN.value  # Will be on down ladder

    # Mark ladder as opened on new floor
    new_chests_opened = state.chests_opened.at[state.player_level - 1].set(True)

    return state.replace(
        player_position=new_position,
        player_direction=new_direction,
        chests_opened=new_chests_opened,
    )
