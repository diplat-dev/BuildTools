from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_PATH = ROOT / "WynnBuilder" / "items_compress.json"
API_URL = "https://api.wynncraft.com/v3/item/database?page={page}"
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
PLAYABLE_TYPES = {"weapon", "armour", "accessory"}

IDENTIFICATION_MAP = {
    "1stSpellCost": "spPct1",
    "2ndSpellCost": "spPct2",
    "3rdSpellCost": "spPct3",
    "4thSpellCost": "spPct4",
    "airDamage": "aDamPct",
    "airMainAttackDamage": "aMdPct",
    "airSpellDamage": "aSdPct",
    "airDefence": "aDefPct",
    "combatExperience": "xpb",
    "criticalDamageBonus": "critDamPct",
    "damage": "damPct",
    "earthDamage": "eDamPct",
    "earthMainAttackDamage": "eMdPct",
    "earthSpellDamage": "eSdPct",
    "earthDefence": "eDefPct",
    "elementalDamage": "rDamPct",
    "elementalMainAttackDamage": "rMdPct",
    "elementalSpellDamage": "rSdPct",
    "elementalDefence": "rDefPct",
    "exploding": "expd",
    "fireDamage": "fDamPct",
    "fireMainAttackDamage": "fMdPct",
    "fireSpellDamage": "fSdPct",
    "fireDefence": "fDefPct",
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
    "neutralMainAttackDamage": "nMdPct",
    "neutralSpellDamage": "nSdPct",
    "poison": "poison",
    "raw1stSpellCost": "spRaw1",
    "raw2ndSpellCost": "spRaw2",
    "raw3rdSpellCost": "spRaw3",
    "raw4thSpellCost": "spRaw4",
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
    "rawNeutralSpellDamage": "nSdRaw",
    "rawSpellDamage": "sdRaw",
    "rawStrength": "str",
    "rawThunderDamage": "tDamRaw",
    "rawThunderMainAttackDamage": "tMdRaw",
    "rawThunderSpellDamage": "tSdRaw",
    "rawWaterDamage": "wDamRaw",
    "rawWaterMainAttackDamage": "wMdRaw",
    "rawWaterSpellDamage": "wSdRaw",
    "reflection": "ref",
    "slowEnemy": "slowEnemy",
    "spellDamage": "sdPct",
    "sprint": "sprint",
    "sprintRegen": "sprintReg",
    "stealing": "eSteal",
    "thorns": "thorns",
    "thunderDamage": "tDamPct",
    "thunderMainAttackDamage": "tMdPct",
    "thunderSpellDamage": "tSdPct",
    "thunderDefence": "tDefPct",
    "walkSpeed": "spd",
    "waterDamage": "wDamPct",
    "waterMainAttackDamage": "wMdPct",
    "waterSpellDamage": "wSdPct",
    "waterDefence": "wDefPct",
    "weakenEnemy": "weakenEnemy",
}

REQUIREMENT_MAP = {
    "strength": "strReq",
    "dexterity": "dexReq",
    "intelligence": "intReq",
    "defence": "defReq",
    "agility": "agiReq",
}

BASE_STAT_MAP = {
    "baseHealth": "hp",
    "baseAirDefence": "aDef",
    "baseEarthDefence": "eDef",
    "baseThunderDefence": "tDef",
    "baseWaterDefence": "wDef",
    "baseFireDefence": "fDef",
}

BASE_DAMAGE_MAP = {
    "baseDamage": "nDam",
    "baseEarthDamage": "eDam",
    "baseThunderDamage": "tDam",
    "baseWaterDamage": "wDam",
    "baseFireDamage": "fDam",
    "baseAirDamage": "aDam",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the official Wynncraft item dataset and rewrite "
            "WynnBuilder/items_compress.json in the local builder format."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to a previously downloaded raw item JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CURRENT_PATH,
        help="Destination for the converted builder item data.",
    )
    parser.add_argument(
        "--current",
        type=Path,
        default=DEFAULT_CURRENT_PATH,
        help="Existing builder item file used to preserve stable ids and display names.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.7,
        help="Delay between paginated API requests when downloading live data.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_roll(value: Any) -> int:
    if isinstance(value, dict):
        return int(value.get("raw", value.get("max", value.get("min", 0))) or 0)
    return int(value or 0)


def clean_lore(raw_text: Any) -> str | None:
    if not raw_text:
        return None
    text = str(raw_text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").strip()
    return text or None


def normalize_icon(icon: Any) -> Any:
    if not isinstance(icon, dict):
        return icon
    normalized = dict(icon)
    value = normalized.get("value")
    if isinstance(value, dict):
        value = dict(value)
        custom_model_data = value.get("customModelData")
        if isinstance(custom_model_data, dict):
            value["customModelData"] = repr(custom_model_data)
        normalized["value"] = value
    return normalized


def derive_armour_material(live_item: dict[str, Any]) -> str | None:
    icon = live_item.get("icon")
    if not isinstance(icon, dict):
        return None
    value = icon.get("value")
    if not isinstance(value, dict):
        return None
    texture_name = str(value.get("name", "") or "")
    if "." not in texture_name:
        return None
    return texture_name.split(".", 1)[1] or None


def major_id_tokens(live_item: dict[str, Any], current_item: dict[str, Any] | None) -> list[str] | None:
    if current_item is not None and current_item.get("majorIds"):
        return list(current_item["majorIds"])
    source = live_item.get("majorIds") or {}
    if not isinstance(source, dict):
        return None
    tokens = []
    for label in source:
        token = re.sub(r"[^A-Za-z0-9]+", "_", str(label).strip()).strip("_").upper()
        if token:
            tokens.append(token)
    return tokens or None


def fetch_live_items(sleep_seconds: float) -> list[dict[str, Any]]:
    page = 1
    items: list[dict[str, Any]] = []
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
                    return items
                if exc.code == 429 and attempt < 7:
                    retry_after = exc.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after else min(20.0, 2.0 * (attempt + 1))
                    time.sleep(wait_seconds)
                    continue
                raise

        if payload is None:
            raise RuntimeError(f"Failed to download page {page}")

        for item in (payload.get("results") or {}).values():
            if isinstance(item, dict):
                items.append(item)

        page += 1
        time.sleep(sleep_seconds)


def load_live_items(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.input is not None:
        raw = load_json(args.input)
    else:
        raw = fetch_live_items(args.sleep_seconds)

    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        results = raw.get("results")
        if isinstance(results, dict):
            return [item for item in results.values() if isinstance(item, dict)]
        items = raw.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    raise ValueError("Unsupported live item payload shape")


def convert_category(live_item: dict[str, Any]) -> str:
    live_type = str(live_item.get("type", "") or "")
    if live_type == "armour":
        return "armor"
    return live_type


def build_identifications(live_item: dict[str, Any]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    identifications = live_item.get("identifications") or {}
    for live_key, raw_value in identifications.items():
        local_key = IDENTIFICATION_MAP.get(str(live_key))
        if local_key is None:
            continue
        mapped[local_key] = normalize_roll(raw_value)
    return mapped


def build_requirements(live_item: dict[str, Any]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    requirements = live_item.get("requirements") or {}
    for live_key, local_key in REQUIREMENT_MAP.items():
        raw_value = int(requirements.get(live_key, 0) or 0)
        if raw_value:
            mapped[local_key] = raw_value
    level = int(requirements.get("level", 0) or 0)
    if level:
        mapped["lvl"] = level
    class_requirement = requirements.get("classRequirement")
    if class_requirement:
        mapped["classReq"] = str(class_requirement)
    return mapped


def build_base_stats(live_item: dict[str, Any], category: str) -> dict[str, Any]:
    base = live_item.get("base") or {}
    mapped: dict[str, Any] = {}
    if category == "weapon":
        for live_key, local_key in BASE_DAMAGE_MAP.items():
            mapped[local_key] = str(base.get(live_key, "0-0") or "0-0")
    else:
        health = int(base.get("baseHealth", 0) or 0)
        if health:
            mapped["hp"] = health

    for live_key, local_key in BASE_STAT_MAP.items():
        if live_key == "baseHealth":
            continue
        value = int(base.get(live_key, 0) or 0)
        if value:
            mapped[local_key] = value
    return mapped


def build_drop_info(live_item: dict[str, Any]) -> dict[str, Any] | None:
    drop_meta = live_item.get("dropMeta")
    if isinstance(drop_meta, dict) and drop_meta:
        return drop_meta
    return None


def build_entry(
    live_item: dict[str, Any],
    current_item: dict[str, Any] | None,
    item_id: int,
) -> dict[str, Any]:
    category = convert_category(live_item)
    entry: dict[str, Any] = {
        "name": str(live_item["internalName"]),
        "category": category,
        "type": str(live_item.get("subType", "") or ""),
        "displayName": current_item.get("displayName") if current_item else str(live_item["internalName"]),
        "id": item_id,
    }

    armour_material = current_item.get("armourMaterial") if current_item else None
    if not armour_material and category == "armor":
        armour_material = derive_armour_material(live_item)
    if armour_material:
        entry["armourMaterial"] = armour_material

    drop_restriction = str(live_item.get("dropRestriction", "") or "")
    if drop_restriction:
        entry["drop"] = drop_restriction

    if current_item is not None and current_item.get("persistent"):
        entry["persistent"] = True

    drop_info = build_drop_info(live_item)
    if drop_info is not None:
        entry["dropInfo"] = drop_info

    if current_item is not None and current_item.get("quest"):
        entry["quest"] = current_item["quest"]
    elif drop_info is not None and str(drop_info.get("type", "") or "").lower() == "quest":
        quest_name = drop_info.get("name")
        if quest_name:
            entry["quest"] = quest_name

    requirements = build_requirements(live_item)
    entry.update(requirements)

    if bool(live_item.get("identified")):
        entry["fixID"] = True

    restriction = str(live_item.get("restriction", "") or "")
    if restriction and restriction.lower() != "none":
        entry["restrict"] = restriction

    if bool(live_item.get("allowCraftsman")):
        entry["allowCraftsman"] = True

    slots = int(live_item.get("powderSlots", 0) or 0)
    if slots:
        entry["slots"] = slots

    lore = clean_lore(live_item.get("lore"))
    if lore:
        entry["lore"] = lore

    icon = normalize_icon(live_item.get("icon"))
    if icon:
        entry["icon"] = icon

    major_ids = major_id_tokens(live_item, current_item)
    if major_ids:
        entry["majorIds"] = major_ids

    if category == "weapon":
        attack_speed = str(live_item.get("attackSpeed", "") or "")
        if attack_speed:
            entry["atkSpd"] = attack_speed.upper()
        average_dps = int(live_item.get("averageDps", 0) or 0)
        if average_dps:
            entry["averageDps"] = average_dps

    base_stats = build_base_stats(live_item, category)
    entry.update(base_stats)

    identifications = build_identifications(live_item)
    entry.update(identifications)

    live_sets = live_item.get("sets") or []
    if live_sets:
        entry["tier"] = "Set"
    else:
        entry["tier"] = str(live_item.get("tier", "") or "").title()

    return entry


def label_for_entry(entry: dict[str, Any]) -> str:
    return str(entry.get("displayName") or entry.get("name") or "")


def normalize_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def sort_key(label: str) -> tuple[str, str]:
    return (normalize_name(label), label.casefold())


def match_sets(
    current_sets: dict[str, dict[str, Any]],
    live_set_items: dict[str, list[str]],
) -> dict[str, str]:
    current_names = list(current_sets)
    current_item_sets = {name: set(current_sets[name].get("items", [])) for name in current_names}
    assignments: dict[str, str] = {}
    used_current: set[str] = set()

    normalized_current: dict[str, list[str]] = {}
    for current_name in current_names:
        normalized_current.setdefault(normalize_name(current_name), []).append(current_name)

    for live_name in sorted(live_set_items, key=str.casefold):
        candidates = normalized_current.get(normalize_name(live_name), [])
        if len(candidates) == 1:
            current_name = candidates[0]
            if current_name not in used_current:
                assignments[live_name] = current_name
                used_current.add(current_name)

    scored_pairs: list[tuple[int, int, int, str, str]] = []
    for live_name, live_items in live_set_items.items():
        if live_name in assignments:
            continue
        live_labels = set(live_items)
        for current_name in current_names:
            if current_name in used_current:
                continue
            current_labels = current_item_sets[current_name]
            overlap = len(live_labels & current_labels)
            if overlap <= 0:
                continue
            union_size = len(live_labels | current_labels)
            name_bonus = 1 if normalize_name(live_name) == normalize_name(current_name) else 0
            scored_pairs.append((overlap, union_size, name_bonus, live_name, current_name))

    scored_pairs.sort(
        key=lambda row: (-row[0], row[1], -row[2], normalize_name(row[3]), normalize_name(row[4]))
    )
    for _overlap, _union_size, _name_bonus, live_name, current_name in scored_pairs:
        if live_name in assignments or current_name in used_current:
            continue
        assignments[live_name] = current_name
        used_current.add(current_name)

    return assignments


def build_sets(
    current_sets: dict[str, dict[str, Any]],
    live_items: list[dict[str, Any]],
    converted_by_name: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    live_set_items: dict[str, list[str]] = {}
    for live_item in live_items:
        item_name = str(live_item["internalName"])
        entry = converted_by_name[item_name]
        label = label_for_entry(entry)
        for set_name in live_item.get("sets") or []:
            live_set_items.setdefault(str(set_name), []).append(label)

    set_matches = match_sets(current_sets, live_set_items)
    converted_sets: dict[str, dict[str, Any]] = {}

    for live_name, labels in sorted(live_set_items.items(), key=lambda row: row[0].casefold()):
        current_name = set_matches.get(live_name)
        output_name = current_name or live_name
        current_set = current_sets.get(current_name, {}) if current_name else {}
        bonuses = current_set.get("bonuses", [])
        current_order = {label: index for index, label in enumerate(current_set.get("items", []))}
        ordered_labels = sorted(
            set(labels),
            key=lambda label: (current_order.get(label, 10**6), sort_key(label)),
        )
        converted_sets[output_name] = {
            "items": ordered_labels,
            "bonuses": bonuses,
        }

    return converted_sets


def main() -> int:
    args = parse_args()
    current_payload = load_json(args.current)
    current_items = current_payload["items"]
    current_sets = current_payload["sets"]
    current_by_name = {item["name"]: item for item in current_items}
    next_id = max(int(item["id"]) for item in current_items) + 1

    live_items = [
        item
        for item in load_live_items(args)
        if str(item.get("type", "") or "") in PLAYABLE_TYPES
    ]

    converted_items: list[dict[str, Any]] = []
    converted_by_name: dict[str, dict[str, Any]] = {}
    for live_item in live_items:
        current_item = current_by_name.get(str(live_item["internalName"]))
        item_id = int(current_item["id"]) if current_item is not None else next_id
        if current_item is None:
            next_id += 1
        entry = build_entry(live_item, current_item, item_id)
        converted_items.append(entry)
        converted_by_name[entry["name"]] = entry

    converted_items.sort(key=lambda item: (-int(item.get("lvl", 0) or 0), sort_key(label_for_entry(item))))

    converted_sets = build_sets(current_sets, live_items, converted_by_name)
    output_payload = {
        "items": converted_items,
        "sets": converted_sets,
    }
    args.output.write_text(
        json.dumps(output_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    current_names = set(current_by_name)
    live_names = {str(item["internalName"]) for item in live_items}
    shared_names = current_names & live_names
    added_names = live_names - current_names
    removed_names = current_names - live_names

    print(f"Wrote {len(converted_items)} items to {args.output}")
    print(f"Shared items kept on stable ids: {len(shared_names)}")
    print(f"New items assigned local ids: {len(added_names)}")
    print(f"Removed items: {len(removed_names)}")
    print(f"Set tables carried forward: {len(converted_sets)}")
    if removed_names:
        print("Removed:", ", ".join(sorted(removed_names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
