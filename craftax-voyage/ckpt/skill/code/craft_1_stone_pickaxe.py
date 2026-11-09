def craft_1_stone_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    # I have 1 wood and 2 stone, need 1 wood + 1 stone for a stone pickaxe
    # Crafting table is in view (2 tiles away)
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE, 1, max_steps=20)
    return state