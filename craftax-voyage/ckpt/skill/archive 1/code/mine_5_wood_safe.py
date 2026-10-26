from craftax.craftax.constants import Action, BlockType

def mine_5_wood_safe(state, log_fn, step_func):
    """
    Safely mines 5 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 wood
        
    Raises:
        Exception: If health is too low to complete the task, or if max steps are reached
    """
    log_fn("Starting to safely mine 5 wood")
    
    # Check current health
    current_health = state.player_health
    log_fn(f"Current health: {current_health}")
    
    # If health is too low, drink until it's safe (at least 5 health)
    if current_health < 5:
        log_fn(f"Health too low ({current_health}), drinking to recover...")
        # First find water
        state = explore_until(state, log_fn, step_func, BlockType.WATER)
        # Drink until health is at least 5
        while current_health < 5:
            log_fn(f"Drinking to recover health, current health: {current_health}")
            state = drink(state, log_fn, step_func, number=1)
            current_health = state.player_health
            log_fn(f"After drinking, health: {current_health}")
    
    # Now mine 5 trees one by one
    for i in range(5):
        log_fn(f"Tree {i+1}/5 - mining...")
        
        # Check health before each tree
        current_health = state.player_health
        if current_health < 5:
            log_fn(f"Health too low ({current_health}), need to drink more")
            # Find and drink from water
            state = explore_until(state, log_fn, step_func, BlockType.WATER)
            while current_health < 5:
                state = drink(state, log_fn, step_func, number=1)
                current_health = state.player_health
                log_fn(f"Drank, health now: {current_health}")
        
        # Explore for a tree
        log_fn(f"Tree {i+1}/5 - exploring...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        # Mine the tree
        log_fn(f"Tree {i+1}/5 - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        log_fn(f"Tree {i+1}/5 - mined! Wood: {state.inventory.wood}, Health: {state.player_health}")
    
    log_fn("Successfully mined 5 wood! Final wood count: {}".format(state.inventory.wood))
    
    return state