# Skill: rest
# Purpose: Rests to recover health when not sleeping
# Required inputs: None
# Preconditions:
#   - Player must have health < max health
#   - Player must be able to interact (not already resting)
# Expected effects:
#   - Player enters rest state
#   - Health recovers slowly
#   - Achievement may be triggered for waking up
# Failure conditions:
#   - Player has maximum health
#   - Player is already resting
# Explanation: Uses REST action from constants.py and update_player_intrinsics from game_logic.py
#           Checks player health from state to determine rest capability
#           Rest recovery is handled by intrinsic decay logic

import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def rest(state: EnvState) -> EnvState:
    """
    Rests to recover health when not sleeping.
    
    Args:
        state: Current environment state
    
    Returns:
        New state with player resting
    
    Raises:
        ValueError: If rest is not possible
    """
    # Check if player has health
    max_health = 8 + state.player_strength
    if state.player_health >= max_health:
        raise ValueError("Player has maximum health")
    
    # Check if player is already resting
    if state.is_resting:
        raise ValueError("Player is already resting")
    
    # Enter rest state
    new_state = state.replace(is_resting=True)
    
    # Apply rest recovery (simplified - in real implementation would use update_player_intrinsics)
    # Health recovery
    new_health = jnp.minimum(state.player_health + 1.0, max_health)
    
    return new_state.replace(
        player_health=new_health,
        is_resting=True,
    )
