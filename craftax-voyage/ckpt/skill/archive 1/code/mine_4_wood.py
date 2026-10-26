from craftax.craftax.constants import BlockType

def mine_4_wood(state, log_fn, step_func):
    """
    Mines 4 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 4 wood
    """
    log_fn("Mining 4 wood from trees")
    
    for i in range(4):
        log_fn(f"Tree {i+1}/4 - exploring for a tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        log_fn(f"Tree {i+1}/4 - mining the tree...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        log_fn(f"Tree {i+1}/4 - done! Have {state.inventory.wood} wood total")
    
    return state