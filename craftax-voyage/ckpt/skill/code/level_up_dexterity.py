def level_up_dexterity(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    # Spend 1 XP to level up dexterity
    state = step_func(Action.LEVEL_UP_DEXTERITY.value)
    return state