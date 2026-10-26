from craftax.craftax.constants import BlockType

def mine_5_wood(state, log_fn, step_func):
    """
    Mines 5 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 wood
    """
    log_fn("Starting to mine 5 wood")
    
    # Get current wood count and convert to Python integer
    current_wood = int(state.inventory.wood)
    log_fn("Current wood count: {}".format(current_wood))
    
    # Calculate how many more wood we need
    wood_needed = 5 - current_wood
    log_fn("Need to mine {} more wood".format(wood_needed))
    
    # If we already have enough or more, we don't need to mine
    if wood_needed <= 0:
        log_fn("Already have {} wood, no need to mine".format(current_wood))
        return state
    
    # Mine the required number of trees at once
    log_fn("Mining {} trees...".format(wood_needed))
    state = mine_block(state, log_fn, step_func, BlockType.TREE, wood_needed)
    
    log_fn("Successfully mined 5 wood total! Final wood count: {}".format(state.inventory.wood))
    
    return state