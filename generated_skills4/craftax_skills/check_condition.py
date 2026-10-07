# Description:
# Checks various game conditions and returns appropriate boolean values.
# Useful for decision-making in higher-level skills.
# Provides helper functions for common checks.


def check_condition(state, condition_type):
    """
    Check a game condition.

    Args:
        state: Current environment state
        condition_type: Type of condition to check (see below)

    Returns:
        bool: True if condition is met
    """
    from craftax.craftax.constants import BlockType

    if condition_type == "has_crafting_table":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.CRAFTING_TABLE.value
                    ):
                        return True
        return False

    elif condition_type == "has_furnace":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.FURNACE.value
                    ):
                        return True
        return False

    elif condition_type == "has_chest":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.CHEST.value
                    ):
                        return True
        return False

    elif condition_type == "has_enchantment_table":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if state.map[state.player_level, block_pos[0], block_pos[1]] in [
                        BlockType.ENCHANTMENT_TABLE_FIRE.value,
                        BlockType.ENCHANTMENT_TABLE_ICE.value,
                    ]:
                        return True
        return False

    elif condition_type == "has_water":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.WATER.value
                    ):
                        return True
        return False

    elif condition_type == "has_tree":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.TREE.value
                    ):
                        return True
        return False

    elif condition_type == "has_stone":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.map[state.player_level, block_pos[0], block_pos[1]]
                        == BlockType.STONE.value
                    ):
                        return True
        return False

    elif condition_type == "has_low_health":
        return state.player_health < 5.0

    elif condition_type == "has_low_food":
        return state.player_food < 3

    elif condition_type == "has_low_drink":
        return state.player_drink < 3

    elif condition_type == "has_low_energy":
        return state.player_energy < 3

    elif condition_type == "has_low_mana":
        return state.player_mana < 3

    elif condition_type == "is_sleeping":
        return state.is_sleeping

    elif condition_type == "is_resting":
        return state.is_resting

    elif condition_type == "has_sword":
        return state.inventory.sword >= 1

    elif condition_type == "has_pickaxe":
        return state.inventory.pickaxe >= 1

    elif condition_type == "has_bow":
        return state.inventory.bow >= 1

    elif condition_type == "has_arrows":
        return state.inventory.arrows >= 1

    elif condition_type == "has_torches":
        return state.inventory.torches >= 1

    elif condition_type == "has_sapling":
        return state.inventory.sapling >= 1

    elif condition_type == "has_coal":
        return state.inventory.coal >= 1

    elif condition_type == "has_iron":
        return state.inventory.iron >= 1

    elif condition_type == "has_diamond":
        return state.inventory.diamond >= 1

    elif condition_type == "has_sapphire":
        return state.inventory.sapphire >= 1

    elif condition_type == "has_ruby":
        return state.inventory.ruby >= 1

    elif condition_type == "has_potion":
        return state.inventory.potions.sum() > 0

    elif condition_type == "has_book":
        return state.inventory.books >= 1

    elif condition_type == "has_learned_fireball":
        return state.learned_spells[0]

    elif condition_type == "has_learned_iceball":
        return state.learned_spells[1]

    elif condition_type == "has_ladder_down":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.item_map[state.player_level, block_pos[0], block_pos[1]]
                        == 2
                    ):  # LADDER_DOWN
                        return True
        return False

    elif condition_type == "has_ladder_up":
        for x in range(OBS_DIM[0]):
            for y in range(OBS_DIM[1]):
                block_pos = state.player_position + jnp.array([x, y])
                if in_bounds(state, block_pos):
                    if (
                        state.item_map[state.player_level, block_pos[0], block_pos[1]]
                        == 3
                    ):  # LADDER_UP
                        return True
        return False

    elif condition_type == "is_boss_vulnerable":
        return (
            state.melee_mobs.mask[state.player_level].sum() == 0
            and state.ranged_mobs.mask[state.player_level].sum() == 0
            and state.boss_timesteps_to_spawn_this_round <= 0
        )

    elif condition_type == "is_fighting_boss":
        return state.player_level == 8

    elif condition_type == "is_on_overworld":
        return state.player_level == 0

    elif condition_type == "is_on_dungeon":
        return state.player_level == 1

    elif condition_type == "is_on_gnomish_mines":
        return state.player_level == 2

    elif condition_type == "is_on_sewers":
        return state.player_level == 3

    elif condition_type == "is_on_vaults":
        return state.player_level == 4

    elif condition_type == "is_on_troll_mines":
        return state.player_level == 5

    elif condition_type == "is_on_fire_realm":
        return state.player_level == 6

    elif condition_type == "is_on_ice_realm":
        return state.player_level == 7

    elif condition_type == "is_on_graveyard":
        return state.player_level == 8

    else:
        raise ValueError(f"Unknown condition type: {condition_type}")
