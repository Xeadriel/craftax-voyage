from craftax.craftax.constants import BlockType

from utils.execution_summary import death_critique, primitive_events, state_diff


def test_primitive_events_filters_steps_and_skill_lines():
    lines = ["Looking for coal", "[mine_block] Start mining 3 COAL block(s) with a budget of 30 steps",
             "[mine_block] Step 0/30: position (1, 2)", "[mine_block] Mined COAL 1/3, coal 0 -> 1",
             "Successfully mined coal", "[not_a_primitive] hi"]
    assert primitive_events(lines) == [lines[1], lines[3]]


def test_state_diff_reports_additions_and_maxima(base_state):
    after = base_state.replace(inventory=base_state.inventory.replace(coal=3), player_drink=7)
    d = state_diff(base_state, after, ["COLLECT_COAL"])
    assert "coal 0 -> 3 (+3)" in d and "drink 9/9 -> 7/9" in d and "COLLECT_COAL" in d


def test_state_diff_shows_placed_table(base_state):
    after = base_state.replace(map=base_state.map.at[0, 24, 25].set(BlockType.CRAFTING_TABLE.value))
    assert "crafting_table" in state_diff(base_state, after, [])


def test_state_diff_no_change(base_state):
    assert "no changes" in state_diff(base_state, base_state, [])


def test_death_critique(base_state):
    s = base_state.replace(player_health=1.0, player_food=0)
    text = death_critique(s, ["[kill_mob] Start hunting MELEE"])
    assert text.startswith("The player died.") and "food 0/9" in text.lower() and "[kill_mob]" in text
