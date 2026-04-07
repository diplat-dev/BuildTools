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
- Automatic level 105 skill allocation using the real `200 total` and `100 max per stat` rules
- Summed item stats, active set bonuses, equip-order checking, and non-crafted damage calculations
- Melee plus a simple spell-damage estimate scaled from the selected weapon's listed DPS
- A summary view with estimated average melee and spell damage
  Note: `spell avg damage` is a heuristic metric for approximating relative spell-build effectiveness. It is useful for comparing builds inside the tool, but it does not directly correspond to a single in-game number.
- A build generator with weighted optimization targets and constraint support using `>`, `<`, or `=`
- Exact search and MCTS search modes, including a stoppable parallel MCTS workflow
- Runtime estimation for the current exact-search configuration
- Searchable metric and gear pickers
- A dark mode toggle
