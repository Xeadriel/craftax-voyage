def craft_1_wood_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    # I have 3 wood, need 1 for a wood pickaxe
    # Crafting table is in view (1 tile away)
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE, 1, max_steps=20)
    return state