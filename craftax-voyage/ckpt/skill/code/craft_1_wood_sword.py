def craft_1_wood_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    # I have 2 wood, need 1 for a wood sword
    # Crafting table is in view (1 tile away)
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD, 1, max_steps=20)
    return state