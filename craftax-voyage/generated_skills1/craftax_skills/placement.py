# Description:
# Provides reusable placement skills for placing blocks and items in the environment.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step

def place_block(state: EnvState, action_func, block_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Places a block of the specified type at the player's current facing direction.
    Returns True if block was placed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if at furnace
        if block_type == BlockType.FURNACE.value:
            if not is_near_block(state, BlockType.FURNACE.value):
                return False
        
        # Check if has materials
        if block_type == BlockType.STONE.value:
            if state.inventory.stone < 1:
                return False
        
        # Check if has materials
        if block_type == BlockType.FURNACE.value:
            if state.inventory.stone < 1:
                return False
        
        # Check if has materials
        if block_type == BlockType.CRAFTING_TABLE.value:
            if state.inventory.wood < 2:
                return False
        
        # Check if has materials
        if block_type == BlockType.TORCH.value:
            if state.inventory.torches < 1:
                return False
        
        # Check if has materials
        if block_type == BlockType.PLANT.value:
            if state.inventory.sapling < 1:
                return False
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] in [BlockType.WATER.value, BlockType.FOUNTAIN.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.GRASS.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.PATH.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.FIRE_GRASS.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.ICE_GRASS.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def place_torch(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Places a torch at the player's current facing direction.
    Returns True if torch was placed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if has torches
        if state.inventory.torches < 1:
            return False
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] in [BlockType.GRASS.value, BlockType.PATH.value, BlockType.FIRE_GRASS.value, BlockType.ICE_GRASS.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def place_plant(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Places a plant (sapling) at the player's current facing direction.
    Returns True if plant was placed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if has sapling
        if state.inventory.sapling < 1:
            return False
        
        # Check if block can be placed
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.GRASS.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False
