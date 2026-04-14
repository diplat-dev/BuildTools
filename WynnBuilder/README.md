# WynnBuilder

Desktop build generation and testing tool for Wynncraft.

## Files

- `build_tester.py`: main application entry point
- `items_compress.json`: local item dataset used by the tool
- `run_build_tester.bat`: convenience launcher for Windows

## Running

From this folder:

```powershell
python .\build_tester.py
```

Or use the local launcher:

```powershell
.\run_build_tester.bat
```

Headless smoke test:

```powershell
python .\build_tester.py --self-test
```

## Included Functionality

- Gear selectors for helmet, chestplate, pants, boots, two rings, bracelet, necklace, and weapon
- Build-level-aware skill allocation using the live beta rules:
  levels `1-100` grant `(level - 1) * 2` base points, and levels `101-121` use the full `200 total` with `100 max per stat`
- Live-beta-style derived stat calculations for total HP, effective HP, HP regen total, effective HP regen, elemental defenses, mana regen total, life steal effectiveness, life per hit, mana per hit, and spell costs
- Summed item stats, active set bonuses, equip-order checking, and non-crafted damage calculations
- Melee damage plus a spell-damage estimate scaled from the selected weapon's listed DPS
- Summary, damage, and stats views that prioritize final computed values instead of raw summed IDs
- `Spell Avg Damage` is intentionally still a heuristic metric for approximating relative spell-build effectiveness while ignoring ability trees. It is useful for comparing builds inside the tool, but it does not directly correspond to a single in-game number.
- A build generator with weighted optimization targets and constraint support using `>`, `<`, or `=`
- Exact search and MCTS search modes, including a stoppable parallel MCTS workflow
- Runtime estimation for the current exact-search configuration
- Searchable metric and gear pickers
- A dark mode toggle
