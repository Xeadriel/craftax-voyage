# Skill: use_chest
# Purpose: Opens and uses a chest to get items
# Required inputs: chest_position (tuple), max_steps (int)
# Preconditions: Player must be near the chest
# Expected effects: Chest is opened, items are retrieved, chest is closed
# Failure conditions: Chest not found, player cannot reach chest
# Explanation: Uses state.map to find chest, state.item_map for item tracking,
#             Action.DO for opening chest interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block, in_bounds

def use_chest(state: EnvState, chest_position: tuple, max_steps: int = 100) -> bool:
    """
    Opens and uses a chest to get items.
    
    Returns True if chest was used successfully, False otherwise.
    """
    # Check if we're near a chest
    if not is_near_block(state, BlockType.CHEST.value):
        return False
    
    # Check if chest is in bounds
    if not in_bounds(state, chest_position):
        return False
    
    # Open the chest by pressing SPACE (Action.DO)
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Move to chest position
        direction = 0
        if chest_position[1] > state.player_position[1]:
            direction = 1
        elif chest_position[1] < state.player_position[1]:
            direction = -1
        elif chest_position[0] > state.player_position[0]:
            direction = 2
        elif chest_position[0] < state.player_position[0]:
            direction = 3
        
        if direction != 0:
            _, new_state, reward, done, info = state.step(key, state, direction, state.default_params)
            state = new_state
        
        # Open the chest
        action = Action.DO.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if chest was opened
        if state.map[state.player_level, chest_position[0], chest_position[1]] == BlockType.PATH.value:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
