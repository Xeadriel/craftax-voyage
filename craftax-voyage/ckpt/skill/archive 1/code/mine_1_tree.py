from craftax.craftax.constants import BlockType

def mine_1_tree(state, log_fn, step_func):
    """
    Mines 1 tree on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 1 tree
    """
    log_fn("Starting to mine 1 tree")
    
    # Explore until we find a tree in sight (though one may already be visible)
    state = explore_until(state, log_fn, step_func, BlockType.TREE)
    
    log_fn("Tree found, mining it...")
    
    # Mine the tree
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn("Tree mined successfully! Wood inventory: {}".format(state.inventory.wood))
    
    return state