# Description:
# Provides reusable combat skills for attacking mobs and managing combat situations.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step
from craftax.craftax.util.game_logic_utils import *

def attack_mob(state: EnvState, action_func, mob_type: BlockType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Attacks a mob of the specified type at the player's current facing direction.
    Returns True if attack was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move towards mob
        direction = action_func
        if direction == Action.LEFT.value:
            direction = (state.player_direction - 1) % 5
        elif direction == Action.RIGHT.value:
            direction = (state.player_direction + 1) % 5
        elif direction == Action.UP.value:
            direction = (state.player_direction + 2) % 5
        elif direction == Action.DOWN.value:
            direction = (state.player_direction + 3) % 5
        
        if direction < 0 or direction >= 5:
            return False
        
        new_position = state.player_position + DIRECTIONS[direction]
        
        if not in_bounds(state, new_position):
            return False
        
        if is_in_mob(state, new_position):
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False


def shoot_arrow(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Shoots an arrow in the direction the player is facing.
    Returns True if arrow was fired, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at crafting table
        if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
            return False
        
        # Check if has bow
        if state.inventory.bow < 1:
            return False
        
        # Check if has arrows
        if state.inventory.arrows < 1:
            return False
        
        # Check if has projectile slots
        if state.player_projectiles.mask[state.player_level].sum() >= StaticEnvParams().max_player_projectiles:
            return False
        
        state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def cast_spell(state: EnvState, action_func, spell_type: BlockType, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Casts a spell of the specified type.
    Returns True if spell was cast, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if has mana
        if state.player_mana < 2:
            return False
        
        # Check if has projectile slots
        if state.player_projectiles.mask[state.player_level].sum() >= StaticEnvParams().max_player_projectiles:
            return False
        
        # Check if learned spell
        if spell_type == BlockType.FIREBALL.value and not state.learned_spells[0]:
            return False
        
        if spell_type == BlockType.ICEBALL.value and not state.learned_spells[1]:
            return False
        
        state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def rest(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Rests to recover health and intrinsics.
    Returns True if resting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.REST.value:
            return False
        
        # Check if health is below maximum
        if state.player_health >= get_max_health(state):
            return False
        
        # Check if food and drink are available
        if state.player_food <= 0 and state.player_drink <= 0:
            return False
        
        state = craftax_step(state.state_rng, state, Action.REST.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def sleep(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Sleeps to recover intrinsics.
    Returns True if sleeping was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.SLEEP.value:
            return False
        
        # Check if energy is below maximum
        if state.player_energy >= get_max_energy(state):
            return False
        
        state = craftax_step(state.state_rng, state, Action.SLEEP.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def fight_boss(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Fights the necromancer boss.
    Returns True if boss was attacked, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        block_position = state.player_position + DIRECTIONS[state.player_direction]
        
        if not in_bounds(state, block_position):
            return False
        
        if is_in_mob(state, block_position):
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Move towards boss
        direction = action_func
        if direction == Action.LEFT.value:
            direction = (state.player_direction - 1) % 5
        elif direction == Action.RIGHT.value:
            direction = (state.player_direction + 1) % 5
        elif direction == Action.UP.value:
            direction = (state.player_direction + 2) % 5
        elif direction == Action.DOWN.value:
            direction = (state.player_direction + 3) % 5
        
        if direction < 0 or direction >= 5:
            return False
        
        new_position = state.player_position + DIRECTIONS[direction]
        
        if not in_bounds(state, new_position):
            return False
        
        if is_in_mob(state, new_position):
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        state = craftax_step(state.state_rng, state, direction, EnvParams(), StaticEnvParams())
    
    return False
