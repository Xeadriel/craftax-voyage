# Skill: cast_spell
# Purpose: Casts a fireball or iceball spell
# Required inputs: spell_type (string: 'fireball' or 'iceball')
# Preconditions:
#   - Player must have learned the spell
#   - Player must have mana >= 2
#   - Player must have projectile slots available
# Expected effects:
#   - Spell is cast in player's facing direction
#   - 2 mana is consumed
#   - Projectile is added to player's projectile slots
#   - Achievement may be triggered for casting
# Failure conditions:
#   - Spell not learned
#   - Insufficient mana
#   - No projectile slots available
# Explanation: Uses cast_spell from game_logic.py which handles spell casting
#           Requires learned_spells from state to determine spell availability
#           Requires mana from inventory to determine casting capability

from craftax.craftax.constants import ProjectileType
from craftax.craftax.craftax_state import EnvState


def cast_spell(state: EnvState, spell_type: str) -> EnvState:
    """
    Casts a fireball or iceball spell.

    Args:
        state: Current environment state
        spell_type: Type of spell to cast ('fireball' or 'iceball')

    Returns:
        New state with spell cast

    Raises:
        ValueError: If spell cannot be cast
    """
    # Map spell type to spell index
    spell_to_index = {"fireball": 0, "iceball": 1}

    if spell_type not in spell_to_index:
        raise ValueError(f"Unknown spell type: {spell_type}")

    spell_index = spell_to_index[spell_type]

    # Check if spell is learned
    if not state.learned_spells[spell_index]:
        raise ValueError(f"Spell {spell_type} not learned")

    # Check if player has mana
    if state.player_mana < 2:
        raise ValueError("Insufficient mana")

    # Check if player has projectile slots available
    if state.player_projectiles.mask[state.player_level].sum() >= 3:
        raise ValueError("No projectile slots available")

    # Get spell direction
    spell_direction = DIRECTIONS[state.player_direction]

    # Cast spell
    new_projectiles, new_directions = _spawn_projectile_logic(
        state,
        state.player_position,
        spell_direction,
        ProjectileType.FIREBALL.value
        if spell_type == "fireball"
        else ProjectileType.ICEBALL.value,
    )

    # Consume mana
    new_mana = state.player_mana - 2

    return state.replace(
        player_projectiles=new_projectiles,
        player_projectile_directions=new_directions,
        player_mana=new_mana,
    )
