def kill_1_skeleton(state, log_fn, step_func):
    from craftax.craftax.constants import MobType
    
    # First, explore until a skeleton (ranged mob) is in view
    # This ensures we have a fresh view and can start hunting immediately
    state = explore_until(state, log_fn, step_func, MobType.RANGED, max_steps=60)
    
    # Then kill the skeleton with a generous step budget
    # Skeletons are ranged mobs with 3 health, stone sword deals 3 damage
    # They keep moving away, so we need more steps to catch and kill
    state = kill_mob(state, log_fn, step_func, MobType.RANGED, max_steps=80)
    
    return state