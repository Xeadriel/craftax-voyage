# Description:
# Attacks a specified mob type at the player's current position.
# Returns True if successfully killed the mob, False otherwise.
# Assumes the mob is within 5 blocks of the player.

from craftax.craftax.constants import (
    Action,
    MobType,
)


def attack_mob(env_step, state, mob_type, max_steps=10):
    """
    Attacks a specified mob type at the player's current position.

    Args:
        env_step: The environment step function
        state: Current environment state
        mob_type: MobType enum value (PASSIVE, MELEE, RANGED)
        max_steps: Maximum number of steps to attempt attack

    Returns:
        True if successfully killed mob, False otherwise
    """
    # Check if there's a mob of the specified type at the player's position
    mob_map = state.mob_map[state.player_level]
    player_position = state.player_position

    # Check for melee mobs
    if mob_type == MobType.MELEE.value:
        melee_mobs = state.melee_mobs
        for mob_index in range(melee_mobs.mask.shape[1]):
            if melee_mobs.mask[state.player_level, mob_index]:
                mob_position = melee_mobs.position[state.player_level, mob_index]
                if (mob_position == player_position).all():
                    # Attack the mob
                    for _ in range(max_steps):
                        state = env_step(None, state, Action.DO.value, None)
                        if state.player_health <= 0:
                            raise ValueError("Player died while attacking mob")
                        if not melee_mobs.mask[state.player_level, mob_index]:
                            return True
                    raise TimeoutError(
                        f"Failed to kill melee mob within {max_steps} steps"
                    )

    # Check for ranged mobs
    elif mob_type == MobType.RANGED.value:
        ranged_mobs = state.ranged_mobs
        for mob_index in range(ranged_mobs.mask.shape[1]):
            if ranged_mobs.mask[state.player_level, mob_index]:
                mob_position = ranged_mobs.position[state.player_level, mob_index]
                if (mob_position == player_position).all():
                    # Attack the mob
                    for _ in range(max_steps):
                        state = env_step(None, state, Action.DO.value, None)
                        if state.player_health <= 0:
                            raise ValueError("Player died while attacking mob")
                        if not ranged_mobs.mask[state.player_level, mob_index]:
                            return True
                    raise TimeoutError(
                        f"Failed to kill ranged mob within {max_steps} steps"
                    )

    raise ValueError(f"No {mob_type} mob found at player position")
