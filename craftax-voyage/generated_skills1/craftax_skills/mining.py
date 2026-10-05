# Description:
# Provides reusable mining skills for gathering resources from the environment.
# Each skill checks for required tools and fails if prerequisites aren't met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step
from craftax.craftax.util.game_logic_utils import *

def mine_block(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Mines a block at the player's current facing direction.
    Returns True if mining was successful, False otherwise.
    Checks for required tool level before attempting to mine.
    """
    for _ in range(step_count):
        # Check if action is valid
        if action_func != Action.DO.value:
            return False
        
        # Get the block position in front of player
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        # Check if block is in bounds
        if not in_bounds(state, block_position):
            return False
        
        # Check if there's a mob at the position
        if is_in_mob(state, block_position):
            return False
        
        # Determine what block type is at the position
        block_type = state.map[state.player_level, block_position[0], block_position[1]]
        
        # Check if we have the required tool level
        if block_type == BlockType.TREE.value:
            # Trees can be mined with any pickaxe
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.STONE.value:
            # Stone requires wood pickaxe (level 1)
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.COAL.value:
            # Coal requires wood pickaxe (level 1)
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.IRON.value:
            # Iron requires stone pickaxe (level 2)
            if state.inventory.pickaxe >= 2:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.DIAMOND.value:
            # Diamond requires iron pickaxe (level 3)
            if state.inventory.pickaxe >= 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.SAPPHIRE.value:
            # Sapphire requires diamond pickaxe (level 4)
            if state.inventory.pickaxe >= 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.RUBY.value:
            # Ruby requires diamond pickaxe (level 4)
            if state.inventory.pickaxe >= 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.STALAGMITE.value:
            # Stalagmite requires any pickaxe (level 1)
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.GRAVE.value or block_type == BlockType.GRAVE2.value or block_type == BlockType.GRAVE3.value:
            # Graves can be mined with any pickaxe
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        elif block_type == BlockType.NECROMANCER.value:
            # Necromancer (boss) requires iron pickaxe (level 3)
            if state.inventory.pickaxe >= 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
        
        else:
            # Other blocks cannot be mined
            return False
    
    return False


def mine_tree(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Mines a tree block at the player's current facing direction.
    Returns True if mining was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == BlockType.TREE.value:
            if state.inventory.pickaxe >= 1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False


def mine_ore(state: EnvState, action_func, ore_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Mines a specific ore type at the player's current facing direction.
    Returns True if mining was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == ore_type.value:
            # Check tool requirements
            if ore_type == BlockType.IRON.value and state.inventory.pickaxe >= 2:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            elif ore_type == BlockType.DIAMOND.value and state.inventory.pickaxe >= 3:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            elif ore_type == BlockType.SAPPHIRE.value and state.inventory.pickaxe >= 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            elif ore_type == BlockType.RUBY.value and state.inventory.pickaxe >= 4:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
            else:
                return False
    
    return False


def mine_sapling(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Mines a sapling from grass at the player's current facing direction.
    Returns True if mining was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == BlockType.GRASS.value:
            # Sapling spawns randomly on grass
            if jax.random.uniform(state.state_rng) < 0.1:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
    
    return False


def mine_water(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Drinks water from a water source at the player's current facing direction.
    Returns True if drinking was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] in [BlockType.WATER.value, BlockType.FOUNTAIN.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def mine_plant(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Eats a ripe plant at the player's current facing direction.
    Returns True if eating was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == BlockType.RIPE_PLANT.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def mine_chest(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Opens a chest at the player's current facing direction.
    Returns True if opening was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == BlockType.CHEST.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def mine_boss(state: EnvState, action_func, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Attacks the necromancer boss at the player's current facing direction.
    Returns True if attacking was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            return False
        
        if state.map[state.player_level, block_position[0], block_position[1]] == BlockType.NECROMANCER.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False
