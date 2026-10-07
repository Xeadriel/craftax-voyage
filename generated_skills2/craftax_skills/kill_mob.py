# Skill: kill_mob
# Purpose: Kills a specified mob type
# Required inputs: mob_type (string), max_steps (int)
# Preconditions: Player must be near the mob, have appropriate weapon
# Expected effects: Mob is killed, experience points gained, achievement unlocked
# Failure conditions: Mob not found, no weapon, mob too far
# Explanation: Uses state.mob_map to find mobs, state.melee_mobs/ranged_mobs for mob data,
#             state.player_health for damage tracking, Action.DO for attacking

import jax
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def kill_mob(state: EnvState, mob_type: str, max_steps: int = 100) -> bool:
    """
    Kills a specified mob type.

    Returns True if mob was killed, False otherwise.
    """
    # Define mob types and their categories
    mob_categories = {
        "zombie": "melee",
        "gnome_warrior": "melee",
        "orc_soldier": "melee",
        "lizard": "melee",
        "knight": "melee",
        "troll": "melee",
        "pigman": "melee",
        "frost_troll": "melee",
        "cow": "passive",
        "bat": "passive",
        "snail": "passive",
        "skeleton": "ranged",
        "gnome_archer": "ranged",
        "orc_mage": "ranged",
        "kobold": "ranged",
        "knight_archer": "ranged",
        "deep_thing": "ranged",
        "fire_elemental": "ranged",
        "ice_elemental": "ranged",
    }

    category = mob_categories.get(mob_type)
    if not category:
        return False

    # Find mobs of the specified type
    mobs_to_kill = []

    if category == "melee":
        for i in range(state.melee_mobs.mask.shape[1]):
            if state.melee_mobs.mask[state.player_level, i]:
                mob_type_id = state.melee_mobs.type_id[state.player_level, i]
                if mob_type_id == mob_categories[mob_type]:
                    mobs_to_kill.append(i)

    elif category == "passive":
        for i in range(state.passive_mobs.mask.shape[1]):
            if state.passive_mobs.mask[state.player_level, i]:
                mob_type_id = state.passive_mobs.type_id[state.player_level, i]
                if mob_type_id == mob_categories[mob_type]:
                    mobs_to_kill.append(i)

    elif category == "ranged":
        for i in range(state.ranged_mobs.mask.shape[1]):
            if state.ranged_mobs.mask[state.player_level, i]:
                mob_type_id = state.ranged_mobs.type_id[state.player_level, i]
                if mob_type_id == mob_categories[mob_type]:
                    mobs_to_kill.append(i)

    if not mobs_to_kill:
        return False

    # Kill mobs by attacking them
    for mob_index in mobs_to_kill:
        for step in range(max_steps):
            key = jax.random.PRNGKey(0)
            # Attack by pressing SPACE (Action.DO)
            _, new_state, reward, done, info = state.step(
                key, state, Action.DO.value, state.default_params
            )
            state = new_state

            # Check if mob is dead
            if category == "melee":
                if not state.melee_mobs.mask[state.player_level, mob_index]:
                    return True
            elif category == "passive":
                if not state.passive_mobs.mask[state.player_level, mob_index]:
                    return True
            elif category == "ranged":
                if not state.ranged_mobs.mask[state.player_level, mob_index]:
                    return True

            # Check if we're stuck
            if step > 0 and step > max_steps // 2:
                return False

    return False
