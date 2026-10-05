# Description:
# Provides reusable crafting skills for creating items at crafting tables and furnaces.
# Each skill checks for required materials and location before attempting to craft.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step

def craft_pickaxe(state: EnvState, action_func, pickaxe_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts a pickaxe of the specified type at a crafting table.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if at furnace (required for iron pickaxe)
        if pickaxe_type == BlockType.IRON.value:
            if not is_near_block(state, BlockType.FURNACE.value):
                return False
        
        # Check materials and tool level
        if pickaxe_type == BlockType.WOOD.value:
            if state.inventory.wood >= 1 and state.inventory.pickaxe < 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif pickaxe_type == BlockType.STONE.value:
            if state.inventory.wood >= 1 and state.inventory.stone >= 1 and state.inventory.pickaxe < 2:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif pickaxe_type == BlockType.IRON.value:
            if state.inventory.wood >= 1 and state.inventory.stone >= 1 and state.inventory.iron >= 1 and state.inventory.coal >= 1 and state.inventory.pickaxe < 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif pickaxe_type == BlockType.DIAMOND.value:
            if state.inventory.wood >= 1 and state.inventory.diamond >= 3 and state.inventory.pickaxe < 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False


def craft_sword(state: EnvState, action_func, sword_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts a sword of the specified type at a crafting table.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check materials and tool level
        if sword_type == BlockType.WOOD.value:
            if state.inventory.wood >= 1 and state.inventory.sword < 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif sword_type == BlockType.STONE.value:
            if state.inventory.stone >= 1 and state.inventory.wood >= 1 and state.inventory.sword < 2:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif sword_type == BlockType.IRON.value:
            if state.inventory.iron >= 1 and state.inventory.wood >= 1 and state.inventory.stone >= 1 and state.inventory.coal >= 1 and state.inventory.sword < 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif sword_type == BlockType.DIAMOND.value:
            if state.inventory.diamond >= 2 and state.inventory.wood >= 1 and state.inventory.sword < 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False


def craft_torch(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts a torch at a crafting table.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check materials
        if state.inventory.coal >= 1 and state.inventory.wood >= 1 and state.inventory.torches < 99:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        else:
            return False
    
    return False


def craft_arrow(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts an arrow at a crafting table.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check materials
        if state.inventory.stone >= 1 and state.inventory.wood >= 1 and state.inventory.arrows < 99:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        else:
            return False
    
    return False


def craft_armour(state: EnvState, action_func, armour_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts armour of the specified type at a crafting table and furnace.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if at furnace
        if not is_near_block(state, BlockType.FURNACE.value):
            return False
        
        # Check materials and armour level
        if armour_type == BlockType.IRON.value:
            if state.inventory.iron >= 3 and state.inventory.coal >= 3 and (state.inventory.armour.sum() < 1):
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif armour_type == BlockType.DIAMOND.value:
            if state.inventory.diamond >= 3 and (state.inventory.armour.sum() < 2):
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False


def craft_item(state: EnvState, action_func, item_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Crafts a generic item of the specified type at a crafting table.
    Returns True if crafting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check materials based on item type
        if item_type == BlockType.WOOD.value:
            if state.inventory.wood >= 1 and state.inventory.pickaxe < 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif item_type == BlockType.STONE.value:
            if state.inventory.stone >= 1 and state.inventory.pickaxe < 2:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif item_type == BlockType.IRON.value:
            if state.inventory.iron >= 1 and state.inventory.pickaxe < 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif item_type == BlockType.DIAMOND.value:
            if state.inventory.diamond >= 1 and state.inventory.pickaxe < 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False
