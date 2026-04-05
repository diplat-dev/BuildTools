# WynnCrafter

Offline Python crafter tool for Wynncraft.

## Files

- `app.py`: desktop application entry point
- `crafter_engine.py`: craft calculation, data loading, and hash encoding logic
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
- Crafted hash import and export
- Warning display for invalid skill usage or level-range mismatches
- Crafted stat summaries and ingredient detail views
- Desktop-friendly `Copy Hash`, `Copy Short`, and `Copy Long` actions
