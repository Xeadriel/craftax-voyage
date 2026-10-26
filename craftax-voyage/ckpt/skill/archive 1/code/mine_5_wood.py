from craftax.craftax.constants import BlockType

def mine_5_wood(state, log_fn, step_func):
    # Check if we already have 5 wood
    if state.inventory.wood >= 5:
        log_fn(f"Already have {state.inventory.wood} wood, no need to mine more")
        return state
    
    # Calculate how many more trees we need to mine
    trees_to_mine = 5 - state.inventory.wood
    log_fn(f"Need to mine {trees_to_mine} more trees to get 5 wood")
    
    # Mine trees one by one until we have 5 wood
    for i in range(trees_to_mine):
        log_fn(f"Step {i+1}: Mining tree {i+1}/{trees_to_mine}")
        
        # Explore until we find a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        log_fn("Found a tree!")
        
        # Mine the tree
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        log_fn(f"Mined tree! Current wood: {state.inventory.wood}")
        
        # Check if we now have 5 wood
        if state.inventory.wood >= 5:
            log_fn(f"Successfully mined 5 wood! Total wood: {state.inventory.wood}")
            break
    
    return state