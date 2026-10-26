# Clean Agent Roles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the curriculum agent the only decision maker (fed by a code-computed situation report), the action agent a literal executor (guarded by an AST code check), and the critic an impartial judge (fed by a code-computed diff and primitive events only).

**Architecture:**
- Two new pure modules hold everything code computes:
  - `utils/situation_report.py`: the player-visible state report.
  - `utils/execution_summary.py`: critic inputs (diff, primitive events, death critique).
- Constants the report needs (recipes, enchant rules, mineable blocks, mob names) move from inside the primitives to module level, so there is one source of truth.
- The agents and `craftax_voyage.py` are rewired to use these modules, and the three prompts are rewritten.

**Tech Stack:** Python 3.12, JAX/Craftax, langchain 0.2.17 (`ChatOpenAI` against vLLM), pytest (new).

**Spec:** `docs/superpowers/specs/2026-10-26-clean-agent-roles-design.md`

## Global Constraints

- **Paths:** all paths below are relative to `craftax-voyage/` (the inner package dir), unless they start with `docs/`.
- **Running tests:** from `craftax-voyage/` with `python -m pytest tests -q`, using the venv at `../.venv` (Python 3.12.14).
- **Player-visible information only.** Every report/diff function reads the world only through `control_primitives/knowledge.py` (`visible_mask`, `is_visible`, `known_blocks`, `known_items`, `visible_mobs`, `ladder_open`) plus the player's own fields (inventory, intrinsics, attributes, achievements, `player_level`, `player_position`). One exception: `state.monsters_killed[level]` for the "kills needed" count (spec §1).
- **No task parsing in code.** No survival override, no mid-task interrupt, no templated skills, no "next upgrades" list.
- **Resources = all mineable blocks:** the keys of `MINEABLE_BLOCKS`. Crafting table and furnace are reported as stations, not resources. Water, fountain and ripe plant are also reported (as drink/food sources); they were in the report mock the user approved.
- **Template escaping:** `prompts/action_template.txt` is rendered with `SystemMessagePromptTemplate.from_template`. Any literal `{` or `}` in it must be written `{{` / `}}`.
- **Do not touch `ckpt/`.** The user archives old checkpoints themselves.
- **Code style:** match the surrounding code (sparse comments, the primitives' docstring format, `log_func` naming inside primitives).
- **Branch:** work on a feature branch, never commit to `master`.

## Review Focus

1. **A skill writes fake primitive lines,** e.g. `log_fn("[mine_block] Successfully mined 3 COAL")`. The critic would treat that as a primitive event. Expected: the code check rejects any `log_fn` call whose first argument is a string or f-string starting with `[`. Test in Task 4.
2. **Braces in `action_template.txt`:** a dict literal or f-string in the new example makes every action call fail with a `KeyError` from the template. Expected: rendering works. Test in Task 5.
3. **The player at the map edge, on a floor where nothing has been seen.** Expected: the report renders with "none seen" / "not seen", with no index errors. Test in Task 2.
4. **The episode ends before the skill took a single step** (`death_state` is `None`). Expected: the death critique is still built, from the state before execution. Test in Task 8.
5. **Resuming from a checkpoint written by the old code:** a `pending_rollout` without `vitals_before`, and no `world_progress.json`. Expected: it resumes with defaults, no `KeyError`. Tests in Tasks 7 and 8.

---

### Task 1: Test harness + shared constants lifted out of the primitives

**Files:**
- Modify: `control_primitives/craft.py` (move the `recipes` dict from inside `craft()`, lines 58-81, to module level)
- Modify: `control_primitives/enchant.py` (move `enchant_actions`, `elements` and `mana_cost`, lines 62-73)
- Modify: `control_primitives/mine_block.py` (move `mineable_blocks`, lines 52-65)
- Modify: `control_primitives/kill_mob.py` (move `mob_names`, lines 70-80)
- Modify: `control_primitives/__init__.py` (add `control_primitive_names`)
- Modify: `pyproject.toml` (add `[project.optional-dependencies] dev = ["pytest"]`)
- Create: `tests/conftest.py`, `tests/test_primitive_constants.py`

**Interfaces:**
- Produces (module-level, the same values as today):
  - `control_primitives.craft.RECIPES: dict[str, tuple[int, dict[str, int], list[str], str, str, int]]`: name → (action value, materials, stations, kind, attribute, level-or-yield)
  - `control_primitives.enchant.ENCHANT_ACTIONS: dict[str, int]`
  - `control_primitives.enchant.ENCHANT_ELEMENTS: dict[str, tuple[int, int, str]]`: element → (enchantment value, table block value, gem field)
  - `control_primitives.enchant.ENCHANT_MANA_COST = 9`
  - `control_primitives.mine_block.MINEABLE_BLOCKS: dict[int, tuple[int, str | None]]`: block value → (required pickaxe level, item)
  - `control_primitives.kill_mob.MOB_NAMES: dict[MobType, list[str]]`
  - `control_primitives.control_primitive_names() -> set[str]`: public top-level `FunctionDef` names from all primitive files, `knowledge.py` included (the same files `load_control_primitives` reads)
- Produces (test fixtures in `tests/conftest.py`):
  - `sys.path` includes the `craftax-voyage/` dir
  - session fixture `base_state` (EnvState from `make_craftax_env_from_name("Craftax-Symbolic-v1", auto_reset=True).reset(jax.random.PRNGKey(0), params)`; the player is at (24, 24) on floor 0, all 99 view cells visible)
  - autouse fixture that calls `knowledge.reset()` before each test

- [ ] **Step 1: Create the branch and install pytest**

Run (from repo root): `git switch -c clean-agent-roles`, then `uv pip install --python .venv/Scripts/python.exe pytest`.
Expected: `python -m pytest --version` prints a version.

- [ ] **Step 2: Write the failing tests** in `tests/test_primitive_constants.py`

```python
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
    from control_primitives.mine_block import MINEABLE_BLOCKS
    from control_primitives.kill_mob import MOB_NAMES
    assert MINEABLE_BLOCKS[BlockType.IRON.value] == (2, "iron")
    assert MOB_NAMES[MobType.MELEE][0] == "Zombie"

def test_control_primitive_names_include_primitives_and_helpers():
    from control_primitives import control_primitive_names
    assert {"sleep", "drink", "craft", "explore_until", "known_blocks", "is_visible"} <= control_primitive_names()

def test_craft_still_validates_with_module_recipes(base_state):
    import pytest
    from control_primitives.craft import craft
    with pytest.raises(Exception, match="wood_pickaxe"):
        craft(base_state, lambda m: None, lambda a: base_state, "golden_hoe")
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/test_primitive_constants.py -q`
Expected: FAIL with `ImportError` (`cannot import name 'RECIPES'`).

- [ ] **Step 4: Move the four tables to module level**

Each primitive module needs a module-level `from craftax.craftax.constants import ...` for what its table references. The function bodies use the module constant instead of the local dict (e.g. `recipes = RECIPES` or direct references). Behaviour stays unchanged.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests -q`
Expected: 5 passed.

- [ ] **Step 6: Commit**

`git add` the four primitives, `pyproject.toml` and `tests/`, then commit with "refactor: lift primitive tables to module level, add pytest harness".

---

### Task 2: Situation report

**Files:**
- Create: `utils/situation_report.py`, `tests/test_situation_report.py`

**Interfaces:**
- Consumes: `RECIPES`, `ENCHANT_*`, `MINEABLE_BLOCKS`, `MOB_NAMES` (Task 1); knowledge functions; `craftax.craftax.util.game_logic_utils.get_max_health/food/drink/energy/mana`; `MONSTERS_KILLED_TO_CLEAR_LEVEL`
- Produces:
  - `FLOOR_NAMES: list[str]`: moved here from `CurriculumAgent.FLOOR_NAMES`, same 9 names
  - `vitals(state) -> dict[str, tuple[float, int]]`: keys `"health","food","drink","energy","mana"` → (current, max)
  - `craftable(state) -> dict[str, list[str]]`: keys `"crafting_table"`, `"crafting_table+furnace"` → `RECIPES` names, in `RECIPES` order
  - `enchantable(state) -> dict[str, list[str]]`: keys `"fire"`, `"ice"` → subset of `["sword", "bow", "armour"]`
  - `blocks_in_view(state) -> dict[str, int]`: lowercase block name → count of visible cells. Covers resources, stations, enchantment tables, water, fountain, ripe plant and chest.
  - `situation_report(state) -> str`

- [ ] **Step 1: Write the failing tests** in `tests/test_situation_report.py`

Build scenarios with `base_state.replace(...)` / `inventory.replace(...)` / `state.map.at[0, r, c].set(...)`.

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_situation_report.py -q`
Expected: FAIL with `ModuleNotFoundError: utils.situation_report`.

- [ ] **Step 3: Implement `utils/situation_report.py`**

What each section must contain (spec §1; the exact layout is the builder's call):
- **Vitals:** `current/max`. Food, drink and energy also get `(can gain up to N)`. Then sleeping/resting.
- **Attributes:** XP, dexterity, strength, intelligence.
- **Threats in view:** melee and ranged mobs from `visible_mobs`, named via `MOB_NAMES`, with distance in tiles (Manhattan). Write "none" when there are none.
- **Equipment:** pickaxe/sword tier names, bow, armour per slot, sword/bow/armour enchantments, learned spells.
- **Inventory:** every field, zeros included.
- **In view now:** `blocks_in_view` plus passive mobs, each with the nearest distance.
- **Seen on this floor:** from `known_blocks`/`known_items`, with the nearest distance. Key ores (coal, iron, diamond, sapphire, ruby) say "not seen" when absent. Chests. Ladder down: not seen / open / blocked with `N more kills needed`.
- **Stations:** crafting table, furnace and both enchantment tables, each "in view (n tiles)" / "seen (n tiles)" / "none seen".
- **Craftable / Enchantable:** the hypothetical lists.
- **Floor:** `N (FLOOR_NAMES[N])`.
- **Missing achievements:** `Achievement` names (lowercased, underscores → spaces) where `achievements[i] == 0`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests -q`
Expected: all pass.

- [ ] **Step 5: Commit**

Commit with "feat: player-visible situation report".

---

### Task 3: Critic inputs (diff, primitive events, death critique)

**Files:**
- Create: `utils/execution_summary.py`, `tests/test_execution_summary.py`

**Interfaces:**
- Consumes: `vitals`, `blocks_in_view`, `FLOOR_NAMES` (Task 2); `control_primitive_names` (Task 1)
- Produces:
  - `primitive_events(lines: list[str]) -> list[str]`: keeps lines matching `^\[(\w+)\] ` whose name is a primitive; drops lines matching `^\[\w+\] Step \d+/\d+`; returns all of them, no truncation
  - `state_diff(before, after, new_achievements: list[str]) -> str`: inventory and equipment changes, vitals before → after with maxima, floor change, new achievements, changed `blocks_in_view` counts. Writes "no changes" when nothing changed.
  - `death_critique(death_state, events: list[str]) -> str`: starts with "The player died."; then the vitals and visible threats of `death_state`, then the events

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run them to verify they fail.** Run: `python -m pytest tests/test_execution_summary.py -q`. Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the three functions in `utils/execution_summary.py`**

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Commit with "feat: critic inputs: state diff, primitive events, death critique".

---

### Task 4: Action-agent code check

**Files:**
- Create: `agents/code_check.py`, `tests/test_code_check.py`
- Modify: `agents/action.py` (`process_ai_message`: run the check after the signature validation)

**Interfaces:**
- Consumes: `control_primitive_names` (Task 1)
- Produces:
  - `agents.code_check.check_skill_code(code: str, program_name: str, reserved_names: set[str]) -> list[str]`: error messages, empty if OK
- `process_ai_message` calls the check with `control_primitive_names() | {"UNKNOWN"}`. If errors come back, it returns the error string `"Error parsing action response (before program execution): " + "; ".join(errors)`, in the same form as the existing parse errors.

The checks (spec §3 plus Review Focus 1):
1. `program_name` in `reserved_names`
2. any `ast.Name` with `Store` context, or a nested `def`, whose name is in `reserved_names`
3. a call to `step_func` with `len(args) + len(keywords) != 1`
4. `BlockType|ItemType|MobType|Action|Achievement` `.X`, where `X` doesn't start with `_` and isn't in that enum's `__members__`
5. a `log_fn` call whose first arg is a `str` constant, or an f-string whose first part is a constant, starting with `[`

- [ ] **Step 1: Write the failing tests**

```python
RESERVED = {"sleep", "drink", "known_blocks", "mine_block", "UNKNOWN"}
OK = "def mine_coal(state, log_fn, step_func):\n    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)\n    state = step_func(Action.NOOP.value)\n    return state\n"

def test_valid_skill_passes():
    assert check_skill_code(OK, "mine_coal", RESERVED) == []

def test_rejects_primitive_name():
    code = "def sleep(state, log_fn, step_func):\n    return sleep(state, log_fn, step_func, max_steps=50)\n"
    assert any("sleep" in e for e in check_skill_code(code, "sleep", RESERVED))

def test_rejects_step_func_with_two_args():
    code = OK.replace("step_func(Action.NOOP.value)", "step_func(state, 5)")
    assert any("step_func" in e for e in check_skill_code(code, "mine_coal", RESERVED))

def test_rejects_unknown_enum_member():
    code = OK.replace("BlockType.COAL", "BlockType.MELEE")
    assert any("MELEE" in e for e in check_skill_code(code, "mine_coal", RESERVED))

def test_rejects_shadowing_helper():
    code = "def f(state, log_fn, step_func):\n    known_blocks = known_blocks(state)\n    return state\n"
    assert any("known_blocks" in e for e in check_skill_code(code, "f", RESERVED))

def test_rejects_fake_primitive_log_line():          # Review Focus 1
    code = "def f(state, log_fn, step_func):\n    log_fn(f\"[mine_block] Successfully mined {1}\")\n    return state\n"
    assert check_skill_code(code, "f", RESERVED) != []
```

- [ ] **Step 2: Run them to verify they fail.** Run: `python -m pytest tests/test_code_check.py -q`. Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `check_skill_code` and hook it into `process_ai_message`**

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Commit with "feat: AST code check for generated skills".

---

### Task 5: Action agent: free re-asks, additive note, prompt rewrite

**Files:**
- Modify: `agents/action.py` (`render_human_message`, `generate_skill`)
- Modify: `prompts/action_template.txt`
- Create: `tests/test_action_agent.py`

**Interfaces:**
- Produces:
  - `ActionAgent.ADDITIVE_AMOUNTS_NOTE = "Amounts in the task are added on top of what you have now (the state above is the starting point)."`: inserted on the line right after `Task: {task}`
  - `ActionAgent.MAX_FIX_ATTEMPTS = 2`: on a parse/validation error, `generate_skill` appends `AIMessage(content)` + `HumanMessage(error)` to `messages` and calls the LLM again, up to 2 extra times. It returns `generation_failed=True` only if all 3 responses fail. Signature unchanged.

- [ ] **Step 1: Write the failing tests** (stub `agent.llm` with a callable returning `AIMessage`)

```python
def test_additive_note_follows_task():
    msg = ActionAgent().render_human_message(task="Drink 6 water", context="", textual_state="S")
    assert "Task: Drink 6 water\n" + ActionAgent.ADDITIVE_AMOUNTS_NOTE in msg.content

def test_bad_then_good_response_is_not_a_failed_generation():
    agent = ActionAgent(); calls = []
    good = "Code:\n```python\ndef f(state, log_fn, step_func):\n    return state\n```"
    agent.llm = lambda messages: (calls.append(messages), AIMessage(content="no code" if len(calls) == 1 else good))[1]
    result = agent.generate_skill(task="t", context="", textual_state="S")
    assert result["generation_failed"] is False and len(calls) == 2
    assert "No Python code block" in calls[1][-1].content

def test_three_bad_responses_fail():
    agent = ActionAgent(); calls = []
    agent.llm = lambda messages: (calls.append(1), AIMessage(content="no code"))[1]
    assert agent.generate_skill(task="t", context="", textual_state="S")["generation_failed"] is True
    assert len(calls) == 3

def test_system_message_renders():                    # Review Focus 2
    content = ActionAgent().render_system_message([]).content
    assert "step_func(Action." in content and "EnvParams" not in content
```

- [ ] **Step 2: Run them to verify they fail.** Run: `python -m pytest tests/test_action_agent.py -q`. Expected: FAIL (no `ADDITIVE_AMOUNTS_NOTE`; the template still contains `EnvParams`).

- [ ] **Step 3: Implement the two code changes and rewrite `prompts/action_template.txt`**

The prompt must contain (spec §3; the wording is the builder's call):
- **Role:** executor only. It does the task as written plus its direct prerequisites on the current floor (materials, tools, crafting stations via primitives). It never changes floors, eats, drinks, sleeps or starts fights the task didn't ask for, and never does a different task. If the task can't be done here, it attempts it as written and lets it fail.
- **Opening example:** replace it with one showing all three patterns:
  - `state = step_func(Action.X.value)`
  - `state = primitive(state, log_fn, step_func, ...)`
  - an additive target (`target = state.inventory.coal + 3`)
- **Rule 3:** checking that you own the *materials/tools* is fine; never skip or shorten the task itself because you already own some of the target.
- **Rule 15:** the general additive-amount rule.
- **Logging:** `log_fn` is for progress notes only. Never state success or failure, and never start a line with `[`.
- **Critique:** the critic's verdict is final. Fix what it reports; never argue the task was already done.
- **Naming:** never name the skill, or any variable, after a program in the list.
- **Knowledge helpers:** one usage line each for `known_blocks(state)` (returns an array) and `is_visible(state, row, col)`.
- **State info:** keep the readable-fields list and the `Inventory` dataclass. Delete the `Mobs`, `EnvState`, `EnvParams` and `StaticEnvParams` dumps.
- **Escaping:** every literal brace is doubled.

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Commit with "feat: action agent executes literally; free re-asks on invalid code".

---

### Task 6: Critic agent on report, diff and events

**Files:**
- Modify: `agents/critic.py` (`render_human_message`, `check_task_success`)
- Modify: `prompts/critic.txt`
- Create: `tests/test_critic_agent.py`

**Interfaces:**
- Produces:
  - `CriticAgent.render_human_message(*, task, report_before, report_after, diff, events, error) -> HumanMessage`
  - `CriticAgent.check_task_success(*, task, report_before, report_after, diff, events, error, max_retries=5) -> tuple[bool, str]`

  `events` is `list[str]`, rendered one per line, or "None" when empty. There is **no** `context` parameter.

- [ ] **Step 1: Write the failing test**

```python
def test_human_message_has_diff_and_events_but_no_context():
    msg = CriticAgent().render_human_message(task="Mine 3 coal", report_before="B", report_after="A",
        diff="coal 0 -> 3 (+3)", events=["[mine_block] Mined COAL 1/3"], error="")
    c = msg.content
    assert "coal 0 -> 3 (+3)" in c and "[mine_block] Mined COAL 1/3" in c
    assert "Context" not in c and "Task: Mine 3 coal" in c
```

- [ ] **Step 2: Run it to verify it fails.** Run: `python -m pytest tests/test_critic_agent.py -q`. Expected: FAIL with `TypeError: unexpected keyword argument 'report_before'`.

- [ ] **Step 3: Implement the change and rewrite `prompts/critic.txt`**

The prompt must contain (spec §4):
- **Inputs:** describe the new ones: reports before/after, the diff, primitive events, error.
- **Sources:** judge only from the diff, the states and the primitive events.
- **Amounts** are additions.
- **Food/drink/energy:** at its maximum after execution = success, even if it was already at the maximum before.
- **Blocked ladder:** a failed descend because the ladder is blocked is a plain fail. The critique states the remaining kills and offers no strategy.
- **Critique content:** what happened and what is still missing for *this* task. No strategy beyond the task, no "game bug" claims, no advice to discard items.
- **Examples:** all rewritten in the new input format.
- **Output format:** keep the existing JSON format.

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Commit with "feat: critic judges from report, diff and primitive events only".

---

### Task 7: Curriculum agent: report, recap, death notice, world progress, QA flag

**Files:**
- Modify: `agents/curriculum.py`
- Modify: `prompts/curriculum.txt`
- Create: `tests/test_curriculum_agent.py`

**Interfaces:**
- Consumes: `situation_report`, `FLOOR_NAMES`, `vitals` (Task 2)
- Produces:
  - `CurriculumAgent(..., use_qa=False)`. With `use_qa` False, `run_qa` is never called, and `get_task_context(task)` returns `""`.
  - `CurriculumAgent.FLOOR_NAMES = FLOOR_NAMES` (import)
  - `CurriculumAgent.DEATH_NOTICE = "You died during the last task. The world was reset: inventory, equipment and floor progress are gone. Learned skills remain."`
  - `propose_next_task(*, env_state, skills="None", max_retries=5)` and `decompose_task(task, env_state, skills="None", max_retries=5)`: the `textual_state` parameter is removed
  - `update_exploration_progress(info)`. `info` always has `task` and `success`. It may also have `critique`, `attempts`, `died`, `vitals_before`, `vitals_after`; missing keys mean `""` / `1` / `False` / `None` / `None`.
    - On success: append the task to `completed_tasks` and `world_progress`.
    - On failure: append it to `failed_tasks`. A death is a failure too, with no special case.
    - On `died`: clear `world_progress`.
    - Always: store the recap in `self.last_turn`.
  - `self.world_progress: list[str]`, persisted to `{ckpt_dir}/curriculum/world_progress.json` and loaded on resume if present
  - `curriculum_observations = ["recap", "state", "context", "skills", "completed_tasks", "world_progress", "failed_tasks"]`, with `default_warmup` holding all seven keys at 0. `"state"` is now `situation_report(env_state)`.
  - The recap block reads `Last turn: "<task>" -> succeeded|failed after N attempt(s); critique: ...; health a/b -> c/d, food ..., drink ..., energy ...`, and starts with `DEATH_NOTICE` when `died`.

- [ ] **Step 1: Write the failing tests** (`CurriculumAgent(ckpt_dir=str(tmp_path))`; stub `qa_llm` with a function that raises)

```python
def test_message_uses_report_not_map(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path))
    agent.completed_tasks = ["Mine 1 wood"]
    agent.qa_llm = lambda m: (_ for _ in ()).throw(AssertionError("QA must be off"))
    c = agent.render_human_message(env_state=base_state).content
    assert "Vitals:" in c and "Map:" not in c

def test_death_clears_world_progress_and_shows_notice(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path))
    agent.update_exploration_progress({"task": "Mine 3 coal", "success": True})
    agent.update_exploration_progress({"task": "Kill 1 zombie", "success": False, "died": True,
        "critique": "The player died.", "attempts": 1,
        "vitals_before": vitals(base_state), "vitals_after": vitals(base_state)})
    assert agent.world_progress == [] and "Kill 1 zombie" in agent.failed_tasks
    assert agent.completed_tasks == ["Mine 3 coal"]
    c = agent.render_human_message(env_state=base_state).content
    assert CurriculumAgent.DEATH_NOTICE in c and 'Last turn: "Kill 1 zombie" -> failed' in c

def test_task_context_empty_without_qa(tmp_path):
    assert CurriculumAgent(ckpt_dir=str(tmp_path)).get_task_context("Mine 1 wood") == ""

def test_resume_without_world_progress_file(tmp_path):        # Review Focus 5
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "curriculum" / "completed_tasks.json").write_text('["Mine 1 wood"]')
    agent = CurriculumAgent(ckpt_dir=str(tmp_path), resume=True)
    assert agent.world_progress == [] and agent.completed_tasks == ["Mine 1 wood"]
```

- [ ] **Step 2: Run them to verify they fail.** Run: `python -m pytest tests/test_curriculum_agent.py -q`. Expected: FAIL.

- [ ] **Step 3: Implement the agent changes and rewrite `prompts/curriculum.txt`**

The prompt must contain (spec §2):
- **Input description:** the report sections, the recap, both progress lists. This replaces the old Map/Inventory format block.
- **Each turn:** vitals vs. maxima and threats come first, and the curriculum anticipates. A task that will take a while must not start with a vital that will run out during it. Then it picks the most valuable progress step: better equipment, new resources, missing achievements, descending when it's the best move.
- **Amounts** are additions and must fit within "can gain up to".
- **Blocked ladder:** schedule kill tasks using "N more kills needed" before proposing a descent.
- **Recap:** use it to judge whether the last choice was good.
- **Examples:** balanced few-shot examples, not survival-heavy.
- **Remove** the old rule 11 (guessing deaths).
- **Keep** the `Reasoning:`/`Task:` response format.

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Commit.** Commit with "feat: curriculum decides from situation report, recap and death notice".

---

### Task 8: Wire it together in `craftax_voyage.py`

**Files:**
- Modify: `craftax_voyage.py` (`step`, `execute_skill`, `rollout`, `learn`, `decompose_task`, `inference`, `CraftaxVoyage.__init__`, `parse_args`)
- Create: `tests/test_rollout.py`

**Interfaces:**
- Consumes: Tasks 2, 3, 6, 7 and `control_primitive_names` (Task 1)
- Produces:
  - **`step`:** stores `self.pre_step_state = self.env_state` before stepping. It is reset to `None` at the start of `execute_skill`.
  - **`execute_skill(skill) -> dict`** with keys:
    - `state_before`
    - `error`
    - `died: bool`: `isinstance(e, EpisodeEnded)`
    - `death_state`: `pre_step_state`, or `state_before` if no step happened
    - `log`: the full log joined, no truncation; `MAX_SKILL_LOG_LINES` is removed
    - `events: list[str]`
    - `new_achievements`
  - **`rollout(task, context, resume=None) -> dict`**: `task`, `success`, `critique`, `attempts`, `died`, `vitals_before`, `vitals_after`, plus `program_name`/`program_code` on success.
    - **On `died`:** the critic is not called; `critique = death_critique(death_state, events)`; return immediately.
    - **Otherwise:** call the critic with `situation_report(state_before)`, `situation_report(self.env_state)`, `state_diff(...)`, `events`, `error`.
    - **Checkpoint:** `vitals_before` is taken at the first attempt and saved in the rollout checkpoint dict. On resume, a missing value falls back to `vitals(self.env_state)`.
  - **`__init__`:** after building the agents, raise `RuntimeError` naming any of `control_primitive_names() | {"UNKNOWN"}` missing from `globals()` (the namespace skills run in).
  - **CLI:** `--use_qa` (`store_true`), passed to `CurriculumAgent(use_qa=...)`.
  - **Call sites:** `propose_next_task` and `decompose_task` calls drop `textual_state`.

- [ ] **Step 1: Write the failing tests**

Build `CraftaxVoyage(args)` with `parse_args`-style defaults and `ckpt_dir=tmp_path`. Stub `action_agent.generate_skill` to return a fixed skill dict, and `critic_agent.check_task_success` to record its kwargs.

```python
def test_death_fails_without_critic_and_ends_rollout(voyage):         # also Review Focus 4
    voyage.action_agent.generate_skill = counting_stub(skill("def f(state, log_fn, step_func):\n    raise EpisodeEnded('x')\n"))
    voyage.critic_agent.check_task_success = must_not_be_called
    info = voyage.rollout("Mine 3 coal", "")
    assert info["died"] is True and info["success"] is False
    assert info["critique"].startswith("The player died.")
    assert voyage.action_agent.generate_skill.calls == 1

def test_critic_gets_report_diff_and_events(voyage):
    voyage.action_agent.generate_skill = counting_stub(skill(
        "def f(state, log_fn, step_func):\n    log_fn('note')\n    state = step_func(Action.NOOP.value)\n    return state\n"))
    seen = {}
    voyage.critic_agent.check_task_success = lambda **kw: (seen.update(kw), (True, ""))[1]
    info = voyage.rollout("Wait", "")
    assert "Vitals:" in seen["report_before"] and isinstance(seen["events"], list)
    assert "note" not in seen["events"] and info["vitals_before"]["health"][1] == 9

def test_resume_without_vitals_before(voyage):                         # Review Focus 5
    voyage.critic_agent.check_task_success = lambda **kw: (True, "")
    voyage.action_agent.generate_skill = counting_stub(skill("def f(state, log_fn, step_func):\n    return state\n"))
    info = voyage.rollout("Wait", "", resume={"next_attempt": 1, "code": "", "error": "", "log": "", "critique": ""})
    assert info["vitals_before"] is not None
```

- [ ] **Step 2: Run them to verify they fail.** Run: `python -m pytest tests/test_rollout.py -q`. Expected: FAIL (`KeyError: 'died'` or a missing kwarg).

- [ ] **Step 3: Implement the wiring**

- [ ] **Step 4: Run all tests.** Run: `python -m pytest tests -q`. Expected: all pass.

- [ ] **Step 5: Smoke-check the report on a real checkpoint (read-only)**

Run: `python -c "from craftax_voyage import load_compressed_pickle; from utils.situation_report import situation_report; print(situation_report(load_compressed_pickle('ckpt/env/env_state.pbz2')['env_state']))"`
Expected: a readable report whose inventory, vitals and floor match `render_craftax_text` of the same state.

- [ ] **Step 6: Commit.** Commit with "feat: wire report, critic inputs, death handling and QA flag into the loop".

---

### Task 9: Hand-off verification (the user runs this on the cluster)

- [ ] **Step 1:** The user archives `ckpt/`, then runs `python craftax_voyage.py --max_iterations 60` with vLLM serving Qwen3.5-4B.
- [ ] **Step 2:** Compare against `testrun.txt`, using the same grep outline as in the analysis:
  - success ratio
  - deaths and their starting vitals
  - `TypeError|AttributeError|UnboundLocalError` count
  - repeated survival tasks
  - deepest floor
  - unique achievements
  - action-agent log lines claiming success: expected 0
  - do-nothing vital tasks passing (the known risk from the spec)
