from craftax.craftax.constants import BlockType

def mine_wood(state, log_fn, step_func):
    """
    Mines 1 wood from a tree on the overworld.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 1 wood
    """
    # Check if we already have wood
    if state.inventory.wood >= 1:
        log_fn("Already have wood, nothing to do")
        return state
    
    log_fn("Looking for a tree to mine")
    
    # Explore until we can see a tree
    state = explore_until(state, log_fn, step_func, BlockType.TREE)
    
    # Mine the tree
    log_fn("Mining a tree")
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    return state