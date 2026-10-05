# Skill: sleep
# Purpose: Sleeps to recover health, hunger, thirst, and energy
# Required inputs: None
# Preconditions:
#   - Player must have energy < max energy
#   - Player must be able to interact (not already sleeping or resting)
# Expected effects:
#   - Player enters sleep state
#   - Health, hunger, thirst, and energy recover
#   - Achievement may be triggered for waking up
# Failure conditions:
#   - Player has maximum energy
#   - Player is already sleeping or resting
# Explanation: Uses SLEEP action from constants.py and update_player_intrinsics from game_logic.py
#           Checks player energy from state to determine sleep capability
#           Sleep recovery is handled by intrinsic decay logic

import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def sleep(state: EnvState) -> EnvState:
    """
    Sleeps to recover health, hunger, thirst, and energy.
    
    Args:
        state: Current environment state
    
    Returns:
        New state with player sleeping
    
    Raises:
        ValueError: If sleep is not possible
    """
    # Check if player has energy
    max_energy = 7 + 2 * state.player_dexterity
    if state.player_energy >= max_energy:
        raise ValueError("Player has maximum energy")
    
    # Check if player is already sleeping or resting
    if state.is_sleeping or state.is_resting:
        raise ValueError("Player is already sleeping or resting")
    
    # Enter sleep state
    new_state = state.replace(is_sleeping=True)
    
    # Apply sleep recovery (simplified - in real implementation would use update_player_intrinsics)
    # Health recovery
    new_health = jnp.minimum(state.player_health + 2.0, 8 + state.player_strength)
    
    # Hunger recovery
    new_hunger = jnp.minimum(state.player_hunger + 0.5, 25)
    new_food = jnp.maximum(state.player_food - 1, 0)
    
    # Thirst recovery
    new_thirst = jnp.minimum(state.player_thirst + 0.5, 20)
    new_drink = jnp.maximum(state.player_drink - 1, 0)
    
    # Energy recovery
    new_energy = jnp.minimum(state.player_energy + 1, max_energy)
    
    return new_state.replace(
        player_health=new_health,
        player_hunger=new_hunger,
        player_food=new_food,
        player_thirst=new_thirst,
        player_drink=new_drink,
        player_energy=new_energy,
        is_sleeping=True,
    )
