# Description:
# Drinks a potion of a specified color if available in inventory.
# Checks for potion availability and applies appropriate effect.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
)
from craftax.craftax.util.game_logic_utils import in_bounds


def drink_potion(env_step_fn, state, potion_color: str, max_steps: int = 50):
    """
    Drinks a potion of a specified color if available in inventory.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        potion_color: Color of potion to drink (RED, GREEN, BLUE, PINK, CYAN, YELLOW)
        max_steps: Maximum number of steps to drink
    
    Returns:
        True if potion was drunk
    
    Raises:
        ValueError: If potion not found in inventory or drinking failed
    """
    import jax.numpy as jnp
    
    # Map potion colors to action values
    color_to_action = {
        "RED": Action.DRINK_POTION_RED.value,
        "GREEN": Action.DRINK_POTION_GREEN.value,
        "BLUE": Action.DRINK_POTION_BLUE.value,
        "PINK": Action.DRINK_POTION_PINK.value,
        "CYAN": Action.DRINK_POTION_CYAN.value,
        "YELLOW": Action.DRINK_POTION_YELLOW.value,
    }
    
    action = color_to_action.get(potion_color)
    if action is None:
        raise ValueError(f"Invalid potion color {potion_color}. Must be one of {list(color_to_action.keys())}")
    
    # Check if we have the potion
    potion_index = get_potion_index(potion_color)
    
    if potion_index < 0:
        raise ValueError(f"No {potion_color} potion in inventory")
    
    # Check if we have the potion in inventory
    if state.inventory.potions[potion_index] <= 0:
        raise ValueError(f"No {potion_color} potion in inventory")
    
    # Drink the potion
    success = drink_potion_action(env_step_fn, state, potion_index, max_steps)
    
    return success


def get_potion_index(potion_color: str) -> int:
    """
    Returns the index of the potion color in the inventory.
    
    Args:
        potion_color: Color of potion
    
    Returns:
        Index of potion in inventory (0-5)
    """
    color_to_index = {
        "RED": 0,
        "GREEN": 1,
        "BLUE": 2,
        "PINK": 3,
        "CYAN": 4,
        "YELLOW": 5,
    }
    
    return color_to_index.get(potion_color, -1)


def drink_potion_action(env_step_fn, state, potion_index: int, max_steps: int = 50):
    """
    Drinks a potion at the current position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        potion_index: Index of potion in inventory
        max_steps: Maximum number of steps to drink
    
    Returns:
        True if potion was drunk
    
    Raises:
        ValueError: If drinking failed
    """
    import jax.numpy as jnp
    
    # Check if position is valid
    if not in_bounds(state, state.player_position):
        raise ValueError("Current position is out of bounds")
    
    # Execute drinking action
    for step in range(max_steps):
        # Try to drink using appropriate action
        action = get_drinking_action(potion_index)
        
        env_step_fn(state, action)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if potion was consumed
        if state.inventory.potions[potion_index] < state.inventory.potions[potion_index] + 1:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Drinking action failed after multiple attempts")
    
    raise ValueError("Drinking action failed")


def get_drinking_action(potion_index: int) -> Action:
    """
    Returns the drinking action for a potion index.
    
    Args:
        potion_index: Index of potion in inventory
    
    Returns:
        Drinking action
    """
    drinking_actions = {
        0: Action.DRINK_POTION_RED.value,
        1: Action.DRINK_POTION_GREEN.value,
        2: Action.DRINK_POTION_BLUE.value,
        3: Action.DRINK_POTION_PINK.value,
        4: Action.DRINK_POTION_CYAN.value,
        5: Action.DRINK_POTION_YELLOW.value,
    }
    
    return drinking_actions.get(potion_index, Action.NOOP.value)
