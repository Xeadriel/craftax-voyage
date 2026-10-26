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
    
    # Mine 5 trees using mine_block which handles exploration internally
    log_fn("Mining 5 trees...")
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 5)
    
    log_fn(f"Successfully mined 5 wood! Final wood count: {state.inventory.wood}")
    
    return state