def craft_wood_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    state = craft(state, log_fn, step_func, "wood_pickaxe", number=1, max_steps=20)
    return state