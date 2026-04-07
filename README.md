# BuildTools

BuildTools is a small collection of standalone Python desktop utilities for Wynncraft theorycrafting. The repository currently includes:

- [`WynnBuilder`](./WynnBuilder/) for build selection, validation, damage/stat summaries, and build generation
- [`WynnCrafter`](./WynnCrafter/) for offline crafted-item simulation, share-hash import/export, and craft optimization
- [`ItemFinder`](./ItemFinder/) for Wynnbuilder-style browsing, filtering, and sorting of items and ingredients

All tools are local-first and ship with the JSON data they need to run.

## Requirements

- Python 3.10 or newer
- A Python installation that includes `tkinter`
- No third-party Python packages

`requirements.txt` is included for compatibility with common Python tooling, but it does not currently install any external dependencies.

## Quick Start

From the repository root on Windows:

```powershell
.\run_wynnbuilder.bat
.\run_wynncrafter.bat
.\run_itemfinder.bat
```

You can also launch the applications directly:

```powershell
python .\WynnBuilder\build_tester.py
python .\WynnCrafter\app.py
python .\ItemFinder\app.py
```

## Verification

Each tool includes a built-in headless smoke test:

```powershell
python .\WynnBuilder\build_tester.py --self-test
python .\WynnCrafter\app.py --self-test
python .\ItemFinder\app.py --self-test
```

## Configuration

No `.env` file, API keys, or external services are required for the current project layout.

## Repository Layout

```text
BuildTools/
  .gitignore
  LICENSE
  README.md
  requirements.txt
  run_itemfinder.bat
  run_wynnbuilder.bat
  run_wynncrafter.bat
  ItemFinder/
    README.md
    app.py
  WynnBuilder/
    README.md
    build_tester.py
    items_compress.json
    run_build_tester.bat
  WynnCrafter/
    README.md
    app.py
    crafter_engine.py
    crafter_optimizer.py
    data/
      ingreds_compress.json
      recipes_compress.json
```

## Project Notes

### WynnBuilder

`WynnBuilder` is the build-planning tool. It provides equipment selection, automatic skill allocation, stat and damage summaries, validation warnings, and exact or MCTS-based generation workflows.

### WynnCrafter

`WynnCrafter` is the offline crafting companion. It supports recipe selection, ingredient slotting, material tiers, weapon attack speed selection, crafted stat summaries, warning output, share-hash import/export, and generator-based craft optimization.

### ItemFinder

`ItemFinder` is the local search browser for vendored WynnBuilder item data and WynnCrafter ingredient data. It uses dataset-specific Wynnbuilder-style search panels, stat-based include/exclude filters, and stat-based sorting with scrollable detail cards.

## License

This project is released under the [MIT License](./LICENSE).
