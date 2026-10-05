# Skill: descend_ladder
# Purpose: Descends to the next level using a ladder
# Required inputs: max_steps (int)
# Preconditions: Player must be at a ladder, monsters killed on current level
# Expected effects: Player moves to next level, ladder closed
# Failure conditions: No ladder, monsters not killed, out of bounds
# Explanation: Uses state.item_map for ladder detection, state.player_level for level tracking,
#             Action.DESCEND for descending action

import jax
import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def descend_ladder(state: EnvState, max_steps: int = 100) -> bool:
    """
    Descends to the next level using a ladder.
    
    Returns True if descent succeeded, False otherwise.
    """
    # Check if we're at a ladder
    if not is_near_block(state, ItemType.LADDER_DOWN.value):
        return False
    
    # Check if we're in bounds
    if not in_bounds(state, state.player_position):
        return False
    
    # Check if monsters have been killed on current level
    if state.monsters_killed[state.player_level] < 8:
        return False
    
    # Descend by pressing DESCEND key
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
        
        # Descend
        action = Action.DESCEND.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if we descended
        if state.player_level > 0:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
