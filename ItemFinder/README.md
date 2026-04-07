# ItemFinder

Offline viewer for browsing WynnBuilder items and WynnCrafter ingredients in one place.

## Files

- `app.py`: desktop application entry point

## Running

From this folder:

```powershell
python .\app.py
```

Or from the workspace root:

```powershell
python .\ItemFinder\app.py
```

Headless smoke test:

```powershell
python .\app.py --self-test
```

## Included Functionality

- Dataset toggle that swaps between a Wynnbuilder-style item search layout and ingredient search layout
- Name search, type toggles, and rarity/star toggles at the top of the page
- Addable stat filters and excluded stat filters using operators like `>=`, `>`, `=`, `<=`, and `<`
- Item-only string filters for text fields like drop info, lore, class requirement, and other visible item info
- Sort controls driven by item or ingredient stats instead of a generic text search
- Scrollable card list showing the title and the meaningful item or ingredient information without exposing the raw JSON payload
- Incremental result loading so the GUI stays responsive with the full dataset
