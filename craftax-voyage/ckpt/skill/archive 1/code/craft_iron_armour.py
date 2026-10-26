def craft_iron_armour(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Starting to craft iron armour")
    
    # Check if we already have iron armour
    if state.inventory.armour is not None and state.inventory.armour.sum() > 0:
        log_fn("Already have iron armour")
        return state
    
    # Mine 2 trees to get enough wood for crafting table (2 wood needed)
    log_fn("Mining 2 trees for crafting table")
    for i in range(2):
        log_fn(f"Tree {i+1}/2 - exploring for a tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        log_fn(f"Tree {i+1}/2 - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        log_fn(f"Tree {i+1}/2 - done. Wood: {state.inventory.wood}")
    
    # Place the crafting table (costs 2 wood)
    log_fn("Placing crafting table (costs 2 wood)")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
    
    # Place the furnace (costs 1 stone) - we need to find a stone block
    log_fn("Placing furnace (costs 1 stone)")
    state = explore_until(state, log_fn, step_func, BlockType.STONE)
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    state = place(state, log_fn, step_func, "furnace")
    log_fn("Furnace placed. Stone remaining: {}".format(state.inventory.stone))
    
    # Mine 3 iron blocks
    log_fn("Mining 3 iron blocks")
    iron_needed = 3 - state.inventory.iron
    if iron_needed > 0:
        for i in range(iron_needed):
            log_fn(f"Iron {i+1}/{iron_needed} - exploring for iron...")
            state = explore_until(state, log_fn, step_func, BlockType.IRON)
            log_fn(f"Iron {i+1}/{iron_needed} - mining...")
            state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
            log_fn(f"Iron {i+1}/{iron_needed} - done. Iron: {state.inventory.iron}")
    
    # Mine 3 coal blocks (we have 5, so this should be fine)
    log_fn("Coal check: have {} coal".format(state.inventory.coal))
    
    # Craft iron armour
    log_fn("Crafting iron armour")
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_ARMOUR)
    
    log_fn("Iron armour crafted successfully!")
    
    return state