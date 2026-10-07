# Description:
# Casts a spell (fireball or iceball) at the player's current position.
# Returns True if successfully cast, False otherwise.
# Assumes the player has learned the spell and has enough mana.

from craftax.craftax.constants import (
    Action,
)


def cast_spell(env_step, state, spell_type, max_steps=5):
    """
    Casts a spell (fireball or iceball).

    Args:
        env_step: The environment step function
        state: Current environment state
        spell_type: "fireball" or "iceball"
        max_steps: Maximum number of steps to attempt casting

    Returns:
        True if successfully cast, False otherwise
    """
    # Check if player has learned the spell
    if spell_type == "fireball" and not state.learned_spells[0]:
        raise ValueError("Player has not learned fireball spell")
    if spell_type == "iceball" and not state.learned_spells[1]:
        raise ValueError("Player has not learned iceball spell")

    # Check if player has enough mana
    if spell_type == "fireball" and state.player_mana < 2:
        raise ValueError("Not enough mana to cast fireball")
    if spell_type == "iceball" and state.player_mana < 2:
        raise ValueError("Not enough mana to cast iceball")

    # Cast the spell
    for _ in range(max_steps):
        if spell_type == "fireball":
            state = env_step(None, state, Action.CAST_FIREBALL.value, None)
        else:
            state = env_step(None, state, Action.CAST_ICEBALL.value, None)

        if state.player_health <= 0:
            raise ValueError("Player died while casting spell")

    return True
