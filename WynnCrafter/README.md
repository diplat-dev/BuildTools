# WynnCrafter

Offline Python crafter tool for Wynncraft.

## Files

- `app.py`: desktop application entry point
- `crafter_engine.py`: craft calculation and data loading
- `data/ingreds_compress.json`: vendored ingredient dataset
- `data/recipes_compress.json`: vendored recipe dataset

## Running

From this folder:

```powershell
python .\app.py
```

Headless smoke test:

```powershell
python .\app.py --self-test
```

## Included Functionality

- Fully offline recipe and ingredient loading
- Recipe type and level-range selection
- Two material tier selectors
- Six ingredient slots
- Weapon attack speed selection
- Warning display for invalid skill usage or level-range mismatches
- Crafted stat summaries and ingredient detail views
- Ingredient optimizer with Exact and MCTS search modes
