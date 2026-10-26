import jax.numpy as jnp

from utils.situation_report import craftable, enchantable, situation_report, vitals


def test_vitals_use_attribute_maxima(base_state):
    s = base_state.replace(player_dexterity=2, player_drink=4)
    assert vitals(s)["drink"] == (4, 11)   # 7 + 2*dex
    assert vitals(s)["health"][1] == 9      # 8 + strength(1)


def test_craftable_respects_materials_and_tier(base_state):
    inv = base_state.inventory.replace(wood=1, stone=1)
    c = craftable(base_state.replace(inventory=inv))
    assert {"wood_pickaxe", "stone_pickaxe", "wood_sword", "stone_sword", "arrow"} <= set(c["crafting_table"])
    assert c["crafting_table+furnace"] == []
    c2 = craftable(base_state.replace(inventory=inv.replace(pickaxe=3)))
    assert "stone_pickaxe" not in c2["crafting_table"]
    c3 = craftable(base_state.replace(inventory=inv.replace(iron=1, coal=1)))
    assert "iron_pickaxe" in c3["crafting_table+furnace"]


def test_enchantable(base_state):
    inv = base_state.inventory.replace(sword=2, ruby=1)
    e = enchantable(base_state.replace(inventory=inv, player_mana=9))
    assert e == {"fire": ["sword"], "ice": []}
    assert enchantable(base_state.replace(inventory=inv, player_mana=8))["fire"] == []
    assert enchantable(base_state.replace(inventory=inv, player_mana=9, sword_enchantment=1))["fire"] == []


def test_report_sections_and_zero_inventory(base_state):
    text = situation_report(base_state)
    for header in ["Vitals:", "Threats in view:", "Equipment:", "Inventory:", "In view now:",
                   "Seen on this floor:", "Stations:", "Craftable", "Enchantable", "Floor: 0 (Overworld)",
                   "Missing achievements:"]:
        assert header in text
    assert "diamond 0" in text.lower()                  # zero entries are listed
    assert "can gain up to 0" in text                    # drink 9/9 at reset
    assert "Map:" not in text


def test_report_shows_threat_with_distance(base_state):
    m = base_state.melee_mobs
    s = base_state.replace(melee_mobs=m.replace(
        position=m.position.at[0, 0].set(jnp.array([24, 26])),
        mask=m.mask.at[0, 0].set(True), type_id=m.type_id.at[0, 0].set(0)))
    text = situation_report(s)
    assert "Zombie" in text and "2 tiles" in text


def test_report_at_map_corner_with_nothing_seen(base_state):          # Review Focus 3
    s = base_state.replace(player_position=jnp.array([0, 0]))
    text = situation_report(s)
    assert "none seen" in text
