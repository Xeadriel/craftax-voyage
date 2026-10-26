import pytest


def test_recipes_match_game_logic():
    from control_primitives.craft import RECIPES

    assert len(RECIPES) == 12
    assert RECIPES["iron_pickaxe"][1] == {"wood": 1, "stone": 1, "iron": 1, "coal": 1}
    assert RECIPES["iron_pickaxe"][2] == ["crafting_table", "furnace"]
    assert RECIPES["diamond_pickaxe"][2] == ["crafting_table"]
    assert RECIPES["iron_armour"][1] == {"iron": 3, "coal": 3}
    assert RECIPES["torch"][5] == 4 and RECIPES["arrow"][5] == 2


def test_enchant_constants():
    from control_primitives.enchant import ENCHANT_ELEMENTS, ENCHANT_MANA_COST

    assert ENCHANT_MANA_COST == 9
    assert ENCHANT_ELEMENTS["fire"][2] == "ruby" and ENCHANT_ELEMENTS["ice"][2] == "sapphire"


def test_mineable_and_mob_names():
    from craftax.craftax.constants import BlockType, MobType
    from control_primitives.kill_mob import MOB_NAMES
    from control_primitives.mine_block import MINEABLE_BLOCKS

    assert MINEABLE_BLOCKS[BlockType.IRON.value] == (2, "iron")
    assert MOB_NAMES[MobType.MELEE][0] == "Zombie"


def test_control_primitive_names_include_primitives_and_helpers():
    from control_primitives import control_primitive_names

    assert {"sleep", "drink", "craft", "explore_until", "known_blocks", "is_visible"} <= control_primitive_names()


def test_craft_still_validates_with_module_recipes(base_state):
    from control_primitives.craft import craft

    with pytest.raises(Exception, match="wood_pickaxe"):
        craft(base_state, lambda m: None, lambda a: base_state, "golden_hoe")
