# Skill: drink_potion
# Purpose: Drinks a specified potion from inventory
# Required inputs: potion_color (string: 'red', 'green', 'blue', 'pink', 'cyan', 'yellow')
# Preconditions:
#   - Player must have the potion in inventory
#   - Player must be able to interact (not sleeping or resting)
# Expected effects:
#   - Potion is consumed from inventory
#   - Health, mana, or energy is modified based on potion type
#   - Achievement may be triggered for drinking
# Failure conditions:
#   - No potion of specified color in inventory
#   - Player is sleeping or resting
# Explanation: Uses drink_potion from game_logic.py which handles potion effects
#           Requires potion from inventory to determine drinking capability
#           Potion effects are permuted each game run (see potion_mapping in state)

import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def drink_potion(state: EnvState, potion_color: str) -> EnvState:
    """
    Drinks a specified potion from inventory.
    
    Args:
        state: Current environment state
        potion_color: Color of potion to drink ('red', 'green', 'blue', 'pink', 'cyan', 'yellow')
    
    Returns:
        New state with potion consumed and stats modified
    
    Raises:
        ValueError: If potion is not available or player cannot drink
    """
    # Map color to potion index
    color_to_index = {
        'red': 0,
        'green': 1,
        'blue': 2,
        'pink': 3,
        'cyan': 4,
        'yellow': 5
    }
    
    if potion_color not in color_to_index:
        raise ValueError(f"Unknown potion color: {potion_color}")
    
    potion_index = color_to_index[potion_color]
    
    # Check if player is sleeping or resting
    if state.is_sleeping or state.is_resting:
        raise ValueError("Cannot drink potion while sleeping or resting")
    
    # Check if potion exists in inventory
    if state.inventory.potions[potion_index] <= 0:
        raise ValueError(f"No {potion_color} potion in inventory")
    
    # Get potion effect from mapping (permuted each game)
    potion_effect_index = state.potion_mapping[potion_index]
    
    # Apply potion effect
    delta_health = 0
    delta_mana = 0
    delta_energy = 0
    
    if potion_effect_index == 0:  # Health
        delta_health = 8
    elif potion_effect_index == 1:  # Health negative
        delta_health = -3
    elif potion_effect_index == 2:  # Mana
        delta_mana = 8
    elif potion_effect_index == 3:  # Mana negative
        delta_mana = -3
    elif potion_effect_index == 4:  # Energy
        delta_energy = 8
    elif potion_effect_index == 5:  # Energy negative
        delta_energy = -3
    
    # Consume potion
    new_inventory = state.inventory.replace(
        potions=state.inventory.potions.at[potion_index].set(
            state.inventory.potions[potion_index] - 1
        )
    )
    
    # Apply effects
    new_health = jnp.minimum(state.player_health + delta_health, 8 + state.player_strength)
    new_mana = jnp.minimum(state.player_mana + delta_mana, 6 + 3 * state.player_intelligence)
    new_energy = jnp.minimum(state.player_energy + delta_energy, 7 + 2 * state.player_dexterity)
    
    return state.replace(
        inventory=new_inventory,
        player_health=new_health,
        player_mana=new_mana,
        player_energy=new_energy,
    )
