from craftax.craftax.constants import MobType

def kill_1_zombie(state, log_fn, step_func):
    """
    Kills 1 zombie on the current floor using the player's melee attack.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the zombie was killed
    """
    log_fn("Starting to kill 1 zombie")
    
    # Zombies are MELEE mobs with type_id 0 on Floor 0
    # The kill_mob function will handle finding and attacking the zombie
    state = kill_mob(state, log_fn, step_func, (MobType.MELEE, 0), max_steps=20)
    
    log_fn(f"Zombie killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state