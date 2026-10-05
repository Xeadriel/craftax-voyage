# Description:
# Provides reusable status management skills for managing player intrinsics and health.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step

def manage_health(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages player health by eating, drinking, and sleeping.
    Returns True if health was managed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if health is below maximum
        if state.player_health >= get_max_health(state):
            return False
        
        # Check if food is available
        if state.player_food > 0:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if drink is available
        if state.player_drink > 0:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if energy is available
        if state.player_energy > 0:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def manage_hunger(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages player hunger by eating food.
    Returns True if hunger was managed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if food is available
        if state.player_food > 0:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if ripe plant is available
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] == BlockType.RIPE_PLANT.value:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def manage_thirst(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages player thirst by drinking water.
    Returns True if thirst was managed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if drink is available
        if state.player_drink > 0:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
        
        # Check if water source is available
        if state.map[state.player_level, state.player_position[0], state.player_position[1]] in [BlockType.WATER.value, BlockType.FOUNTAIN.value]:
            state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
            return True
    
    return False


def manage_energy(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages player energy by sleeping.
    Returns True if energy was managed, False otherwise.
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


def manage_mana(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages player mana by resting or sleeping.
    Returns True if mana was managed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.REST.value:
            return False
        
        # Check if mana is below maximum
        if state.player_mana >= get_max_mana(state):
            return False
        
        state = craftax_step(state.state_rng, state, Action.REST.value, EnvParams(), StaticEnvParams())
        return True
    
    return False


def manage_intrinsics(state: EnvState, action_func, step_count: int = 10, max_steps: int = 100) -> bool:
    """
    Manages all player intrinsics (health, hunger, thirst, energy, mana).
    Returns True if intrinsics were managed, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if any intrinsic needs management
        if state.player_health < get_max_health(state):
            if state.player_food > 0 or state.player_drink > 0 or state.player_energy > 0:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
        
        if state.player_hunger > 25:
            if state.player_food > 0:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
        
        if state.player_thirst > 20:
            if state.player_drink > 0:
                state = craftax_step(state.state_rng, state, Action.DO.value, EnvParams(), StaticEnvParams())
                return True
        
        if state.player_energy > 30:
            state = craftax_step(state.state_rng, state, Action.SLEEP.value, EnvParams(), StaticEnvParams())
            return True
        
        if state.player_mana > 30:
            state = craftax_step(state.state_rng, state, Action.REST.value, EnvParams(), StaticEnvParams())
            return True
    
    return False
