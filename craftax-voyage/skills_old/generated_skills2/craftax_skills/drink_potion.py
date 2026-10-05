# Skill: drink_potion
# Purpose: Drinks a specified potion
# Required inputs: potion_type (string), max_steps (int)
# Preconditions: Player must have the potion in inventory
# Expected effects: Potion is consumed, corresponding intrinsic is restored
# Failure conditions: No potion in inventory, invalid potion type
# Explanation: Uses state.inventory for potion availability, Action.DRINK_* for drinking interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState

def drink_potion(state: EnvState, potion_type: str, max_steps: int = 100) -> bool:
    """
    Drinks a specified potion.
    
    Returns True if potion was drunk, False otherwise.
    """
    # Define potion types and their effects
    potion_effects = {
        "red": 0,
        "green": 1,
        "blue": 2,
        "pink": 3,
        "cyan": 4,
        "yellow": 5,
    }
    
    effect_index = potion_effects.get(potion_type)
    if effect_index is None:
        return False
    
    # Check if we have the potion in inventory
    potion_index = effect_index
    if state.inventory.potions[potion_index] <= 0:
        return False
    
    # Drink the potion by pressing the appropriate key
    drink_keys = {
        "red": Action.DRINK_POTION_RED.value,
        "green": Action.DRINK_POTION_GREEN.value,
        "blue": Action.DRINK_POTION_BLUE.value,
        "pink": Action.DRINK_POTION_PINK.value,
        "cyan": Action.DRINK_POTION_CYAN.value,
        "yellow": Action.DRINK_POTION_YELLOW.value,
    }
    
    drink_key = drink_keys.get(potion_type)
    if not drink_key:
        return False
    
    # Drink the potion
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Drink
        action = drink_key
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if potion was drunk
        if state.inventory.potions[potion_index] <= 0:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
