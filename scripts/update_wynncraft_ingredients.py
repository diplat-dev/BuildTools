from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_PATH = ROOT / "WynnCrafter" / "data" / "ingreds_compress.json"
API_URL = "https://api.wynncraft.com/v3/item/database?page={page}"
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}

IDENTIFICATION_MAP = {
    "2ndSpellCost": "spPct2",
    "airDamage": "aDamPct",
    "airDefence": "aDefPct",
    "airSpellDamage": "aSdPct",
    "combatExperience": "xpb",
    "earthDamage": "eDamPct",
    "earthDefence": "eDefPct",
    "earthSpellDamage": "eSdPct",
    "elementalDamage": "rDamPct",
    "elementalDefence": "rDefPct",
    "elementalSpellDamage": "rSdPct",
    "exploding": "expd",
    "fireDamage": "fDamPct",
    "fireDefence": "fDefPct",
    "fireSpellDamage": "fSdPct",
    "gatherSpeed": "gSpd",
    "gatherXpBonus": "gXp",
    "healingEfficiency": "healPct",
    "healthRegen": "hprPct",
    "healthRegenRaw": "hprRaw",
    "jumpHeight": "jh",
    "knockback": "kb",
    "lifeSteal": "ls",
    "lootBonus": "lb",
    "lootQuality": "lq",
    "mainAttackDamage": "mdPct",
    "mainAttackRange": "mainAttackRange",
    "manaRegen": "mr",
    "manaSteal": "ms",
    "neutralDamage": "nDamPct",
    "poison": "poison",
    "rawAgility": "agi",
    "rawAirDamage": "aDamRaw",
    "rawAirMainAttackDamage": "aMdRaw",
    "rawAirSpellDamage": "aSdRaw",
    "rawAttackSpeed": "atkTier",
    "rawDefence": "def",
    "rawDexterity": "dex",
    "rawEarthDamage": "eDamRaw",
    "rawEarthMainAttackDamage": "eMdRaw",
    "rawEarthSpellDamage": "eSdRaw",
    "rawFireDamage": "fDamRaw",
    "rawFireMainAttackDamage": "fMdRaw",
    "rawFireSpellDamage": "fSdRaw",
    "rawHealth": "hpBonus",
    "rawIntelligence": "int",
    "rawMainAttackDamage": "mdRaw",
    "rawMaxMana": "maxMana",
    "rawNeutralDamage": "nDamRaw",
    "rawNeutralMainAttackDamage": "nMdRaw",
    "rawSpellDamage": "sdRaw",
    "rawStrength": "str",
    "rawThunderDamage": "tDamRaw",
    "rawThunderMainAttackDamage": "tMdRaw",
    "rawThunderSpellDamage": "tSdRaw",
    "rawWaterDamage": "wDamRaw",
    "rawWaterMainAttackDamage": "wMdRaw",
    "rawWaterSpellDamage": "wSdRaw",
    "reflection": "ref",
    "spellDamage": "sdPct",
    "sprint": "sprint",
    "sprintRegen": "sprintReg",
    "stealing": "eSteal",
    "thorns": "thorns",
    "thunderDamage": "tDamPct",
    "thunderDefence": "tDefPct",
    "walkSpeed": "spd",
    "waterDamage": "wDamPct",
    "waterDefence": "wDefPct",
    "waterSpellDamage": "wSdPct",
}

SKILL_MAP = {
    "alchemism": "ALCHEMISM",
    "armouring": "ARMOURING",
    "cooking": "COOKING",
    "jeweling": "JEWELING",
    "scribing": "SCRIBING",
    "tailoring": "TAILORING",
    "weaponsmithing": "WEAPONSMITHING",
    "woodworking": "WOODWORKING",
}

ITEM_ONLY_MAP = {
    "durabilityModifier": "dura",
    "strengthRequirement": "strReq",
    "dexterityRequirement": "dexReq",
    "intelligenceRequirement": "intReq",
    "defenceRequirement": "defReq",
    "agilityRequirement": "agiReq",
}

CONSUMABLE_ONLY_MAP = {
    "duration": "dura",
    "charges": "charges",
}

POSITION_KEYS = ("left", "right", "above", "under", "touching", "notTouching")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the official Wynncraft ingredient dataset and rewrite "
            "WynnCrafter/data/ingreds_compress.json in the local crafter format."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to a previously downloaded raw ingredient JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CURRENT_PATH,
        help="Destination for the converted ingredient data.",
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=DEFAULT_CURRENT_PATH,
        help="Existing crafter ingredient file used to preserve display names and stable ids.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.7,
        help="Delay between paginated API requests when downloading live data.",
    )
    return parser.parse_args()


def fetch_live_ingredients(sleep_seconds: float) -> list[dict[str, Any]]:
    page = 1
    ingredients: list[dict[str, Any]] = []
    while True:
        url = API_URL.format(page=page)
        payload: dict[str, Any] | None = None
        for attempt in range(8):
            try:
                request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 400:
                    return ingredients
                if exc.code == 429 and attempt < 7:
                    retry_after = exc.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after else min(20.0, 2.0 * (attempt + 1))
                    time.sleep(wait_seconds)
                    continue
                raise

        if payload is None:
            raise RuntimeError(f"Failed to download page {page}")

        for item in (payload.get("results") or {}).values():
            if isinstance(item, dict) and item.get("type") == "ingredient":
                ingredients.append(item)

        page += 1
        time.sleep(sleep_seconds)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_roll(value: Any) -> tuple[int, int]:
    if isinstance(value, dict):
        minimum = int(value.get("min", value.get("raw", 0)) or 0)
        maximum = int(value.get("max", value.get("raw", 0)) or 0)
        return minimum, maximum
    numeric = int(value or 0)
    return numeric, numeric


def parse_tier(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "")
    digits = [char for char in text if char.isdigit()]
    if digits:
        return int(digits[-1])
    return 0


def build_ids(live_item: dict[str, Any]) -> dict[str, dict[str, int]]:
    ids: dict[str, dict[str, int]] = {}
    identifications = live_item.get("identifications") or {}
    for live_key in sorted(identifications):
        local_key = IDENTIFICATION_MAP.get(live_key)
        if local_key is None:
            continue
        minimum, maximum = normalize_roll(identifications[live_key])
        ids[local_key] = {"minimum": minimum, "maximum": maximum}
    return ids


def build_item_ids(live_item: dict[str, Any]) -> dict[str, int]:
    mapped: dict[str, int] = {value: 0 for value in ITEM_ONLY_MAP.values()}
    for live_key, local_key in ITEM_ONLY_MAP.items():
        raw_value = int((live_item.get("itemOnlyIDs") or {}).get(live_key, 0) or 0)
        if local_key == "dura":
            mapped[local_key] = int(raw_value / 1000)
        else:
            mapped[local_key] = raw_value
    return mapped


def build_consumable_ids(live_item: dict[str, Any]) -> dict[str, int]:
    mapped: dict[str, int] = {value: 0 for value in CONSUMABLE_ONLY_MAP.values()}
    for live_key, local_key in CONSUMABLE_ONLY_MAP.items():
        mapped[local_key] = int((live_item.get("consumableOnlyIDs") or {}).get(live_key, 0) or 0)
    return mapped


def build_pos_mods(live_item: dict[str, Any]) -> dict[str, int]:
    source = live_item.get("ingredientPositionModifiers") or {}
    not_touching = source.get("notTouching", source.get("not_touching", 0))
    mapped = {
        "left": int(source.get("left", 0) or 0),
        "right": int(source.get("right", 0) or 0),
        "above": int(source.get("above", 0) or 0),
        "under": int(source.get("under", 0) or 0),
        "touching": int(source.get("touching", 0) or 0),
        "notTouching": int(not_touching or 0),
    }
    return mapped


def convert_skills(live_item: dict[str, Any]) -> list[str]:
    skills = []
    for skill in (live_item.get("requirements") or {}).get("skills") or []:
        skills.append(SKILL_MAP.get(str(skill), str(skill).upper()))
    return skills


def build_converted_entry(
    live_item: dict[str, Any],
    current_item: dict[str, Any] | None,
    ingredient_id: int,
) -> dict[str, Any]:
    name = str(live_item["internalName"])
    display_name = current_item.get("displayName", name) if current_item else name
    requirements = live_item.get("requirements") or {}
    entry: dict[str, Any] = {}
    entry["name"] = name
    entry["type"] = "ingredient"
    entry["lvl"] = int(requirements.get("level", 0) or 0)
    entry["skills"] = convert_skills(live_item)
    entry["icon"] = live_item.get("icon") or {}
    entry["ids"] = build_ids(live_item)
    entry["tier"] = parse_tier(live_item.get("tier"))
    entry["consumableIDs"] = build_consumable_ids(live_item)
    entry["posMods"] = build_pos_mods(live_item)
    entry["itemIDs"] = build_item_ids(live_item)
    entry["displayName"] = display_name
    entry["id"] = ingredient_id
    return entry


def main() -> int:
    args = parse_args()
    current_items = load_json(args.current)
    current_by_name = {item["name"]: item for item in current_items}
    current_ids = {int(item["id"]) for item in current_items}
    next_id = max(current_ids, default=-1) + 1

    if args.input is not None:
        live_items = load_json(args.input)
    else:
        live_items = fetch_live_ingredients(args.sleep_seconds)

    live_items = [item for item in live_items if item.get("type") == "ingredient"]
    live_by_name = {item["internalName"]: item for item in live_items}

    converted: list[dict[str, Any]] = []
    for live_item in live_items:
        current_item = current_by_name.get(live_item["internalName"])
        if current_item is not None:
            ingredient_id = int(current_item["id"])
        else:
            ingredient_id = next_id
            next_id += 1
        converted.append(build_converted_entry(live_item, current_item, ingredient_id))

    converted.sort(key=lambda item: (-int(item["lvl"]), str(item["displayName"]).casefold()))

    args.output.write_text(
        json.dumps(converted, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    current_names = set(current_by_name)
    live_names = set(live_by_name)
    shared_names = current_names & live_names
    added_names = live_names - current_names
    removed_names = current_names - live_names

    print(f"Wrote {len(converted)} ingredients to {args.output}")
    print(f"Shared ingredients kept on stable ids: {len(shared_names)}")
    print(f"New ingredients assigned local ids: {len(added_names)}")
    print(f"Removed ingredients: {len(removed_names)}")
    if removed_names:
        print("Removed:", ", ".join(sorted(removed_names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
