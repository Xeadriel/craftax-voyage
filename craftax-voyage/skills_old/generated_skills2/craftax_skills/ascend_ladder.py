# Skill: ascend_ladder
# Purpose: Ascends to the previous level using a ladder
# Required inputs: max_steps (int)
# Preconditions: Player must be at a ladder
# Expected effects: Player moves to previous level, ladder opened
# Failure conditions: No ladder, out of bounds
# Explanation: Uses state.item_map for ladder detection, state.player_level for level tracking,
#             Action.ASCEND for ascending action

import jax
import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def ascend_ladder(state: EnvState, max_steps: int = 100) -> bool:
    """
    Ascends to the previous level using a ladder.
    
    Returns True if ascent succeeded, False otherwise.
    """
    # Check if we're at a ladder
    if not is_near_block(state, ItemType.LADDER_UP.value):
        return False
    
    # Check if we're in bounds
    if not in_bounds(state, state.player_position):
        return False
    
    # Check if we're not on the first level
    if state.player_level <= 0:
        return False
    
    # Ascend by pressing ASCEND key
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Move to ladder position
        direction = 0
        if state.player_position[1] > state.player_position[1]:
            direction = 1
        elif state.player_position[1] < state.player_position[1]:
            direction = -1
        elif state.player_position[0] > state.player_position[0]:
            direction = 2
        elif state.player_position[0] < state.player_position[0]:
            direction = 3
        
        if direction != 0:
            _, new_state, reward, done, info = state.step(key, state, direction, state.default_params)
            state = new_state
        
        # Ascend
        action = Action.ASCEND.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if we ascended
        if state.player_level > 0:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
