from __future__ import annotations

import argparse
import json
import re
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
ITEM_DATA_PATH = WORKSPACE_ROOT / "WynnBuilder" / "items_compress.json"
INGREDIENT_DATA_PATH = WORKSPACE_ROOT / "WynnCrafter" / "data" / "ingreds_compress.json"

APP_TITLE = "ItemFinder"
WINDOW_SIZE = "1640x980"
INITIAL_RESULT_LIMIT = 50
RESULT_BATCH_SIZE = 50
NUMERIC_OPERATORS = (">=", ">", "=", "<=", "<")
SORT_ORDERS = ("Descending", "Ascending")

THEME = {
    "page_bg": "#f6f6f6",
    "panel_bg": "#ffffff",
    "panel_alt": "#fafafa",
    "line": "#d6d6d6",
    "line_soft": "#e7e7e7",
    "text": "#202124",
    "muted": "#63666a",
    "accent": "#0d6efd",
    "accent_soft": "#e7f0ff",
    "button_bg": "#f3f3f3",
    "button_active": "#e7edf9",
}

ITEM_TYPE_OPTIONS = (
    ("Helmet", "helmet"),
    ("Chestplate", "chestplate"),
    ("Leggings", "leggings"),
    ("Boots", "boots"),
    ("Ring", "ring"),
    ("Bracelet", "bracelet"),
    ("Necklace", "necklace"),
    ("Wand", "wand"),
    ("Spear", "spear"),
    ("Bow", "bow"),
    ("Dagger", "dagger"),
    ("Relik", "relik"),
)
ITEM_RARITY_OPTIONS = (
    ("N", "normal"),
    ("U", "unique"),
    ("S", "set"),
    ("R", "rare"),
    ("L", "legendary"),
    ("F", "fabled"),
    ("M", "mythic"),
)
INGREDIENT_TYPE_OPTIONS = (
    ("Armouring", "armouring"),
    ("Tailoring", "tailoring"),
    ("Weaponsmithing", "weaponsmithing"),
    ("Woodworking", "woodworking"),
    ("Jeweling", "jeweling"),
    ("Cooking", "cooking"),
    ("Alchemism", "alchemism"),
    ("Scribing", "scribing"),
)
INGREDIENT_STAR_OPTIONS = (
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
)
ITEM_TIER_RANKS = {
    "normal": 0.0,
    "unique": 1.0,
    "set": 2.0,
    "rare": 3.0,
    "legendary": 4.0,
    "fabled": 5.0,
    "mythic": 6.0,
}

ELEMENT_LABELS = {
    "n": "Neutral",
    "e": "Earth",
    "t": "Thunder",
    "w": "Water",
    "f": "Fire",
    "a": "Air",
    "r": "Rainbow",
}
SKILL_LABELS = {
    "str": "Strength",
    "dex": "Dexterity",
    "int": "Intelligence",
    "def": "Defense",
    "agi": "Agility",
}
OVERRIDE_LABELS = {
    "atkSpd": "Attack Speed",
    "atkTier": "Attack Speed Tier",
    "averageDps": "Average DPS",
    "classReq": "Class Requirement",
    "dropInfo": "Drop Info",
    "allowCraftsman": "Allow Craftsman",
    "fixID": "Fixed IDs",
    "gXp": "Gather XP Bonus",
    "gSpd": "Gather Speed",
    "xpb": "Combat XP Bonus",
    "lq": "Loot Quality",
    "eSteal": "Emerald Steal",
    "expd": "Exploding",
    "spd": "Walk Speed",
    "jh": "Jump Height",
    "kb": "Knockback",
    "mr": "Mana Regen",
    "ms": "Mana Steal",
    "ls": "Life Steal",
    "lb": "Loot Bonus",
    "damPct": "Damage %",
    "damRaw": "Damage Raw",
    "sdPct": "Spell Damage %",
    "sdRaw": "Spell Damage Raw",
    "mdPct": "Main Attack Damage %",
    "mdRaw": "Main Attack Damage Raw",
    "hprPct": "Health Regen %",
    "hprRaw": "Health Regen Raw",
    "hpBonus": "Health Bonus",
    "healPct": "Heal %",
    "mainAttackRange": "Main Attack Range",
    "maxMana": "Max Mana",
    "lvl": "Level",
    "dura": "Durability",
}

ITEM_META_KEYS = (
    "lvl",
    "tier",
    "type",
    "category",
    "armourMaterial",
    "classReq",
    "atkSpd",
    "averageDps",
    "slots",
    "drop",
    "dropInfo",
    "restrict",
    "quest",
    "allowCraftsman",
    "fixID",
)
ITEM_REQUIREMENT_KEYS = ("strReq", "dexReq", "intReq", "defReq", "agiReq")
ITEM_DAMAGE_KEYS = ("nDam", "eDam", "tDam", "wDam", "fDam", "aDam")
ITEM_INTERNAL_SKIP = {"name", "displayName", "id", "icon", "lore", "majorIds"}
RANGE_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)\s*$")
ELEMENT_STAT_PATTERN = re.compile(r"^(?P<element>[netwfar])(?P<body>Dam|Def|Md|Sd)(?P<suffix>Pct|Raw)?$")
SKILL_REQ_PATTERN = re.compile(r"^(?P<skill>str|dex|int|def|agi)Req$")
SPELL_COST_PATTERN = re.compile(r"^sp(?P<body>Pct|Raw)(?P<slot>[1-4])(?P<final>Final)?$")


@dataclass(frozen=True)
class StatOption:
    key: str
    label: str


@dataclass(frozen=True)
class DisplayRow:
    label: str
    value: str


@dataclass(frozen=True)
class DisplaySection:
    title: str
    rows: tuple[DisplayRow, ...]


@dataclass
class FinderRecord:
    dataset: str
    title: str
    subtitle: str
    type_tags: tuple[str, ...]
    rarity_tag: str
    numeric_stats: dict[str, float]
    string_stats: dict[str, tuple[str, ...]]
    sections: tuple[DisplaySection, ...]
    search_blob: str


@dataclass
class DatasetBundle:
    key: str
    heading: str
    type_label: str
    type_options: tuple[tuple[str, str], ...]
    rarity_label: str
    rarity_options: tuple[tuple[str, str], ...]
    records: list[FinderRecord]
    numeric_options: tuple[StatOption, ...]
    string_options: tuple[StatOption, ...]
    sort_options: tuple[StatOption, ...]
    default_sort_key: str

    @property
    def numeric_labels(self) -> tuple[str, ...]:
        return tuple(option.label for option in self.numeric_options)

    @property
    def string_labels(self) -> tuple[str, ...]:
        return tuple(option.label for option in self.string_options)

    @property
    def sort_labels(self) -> tuple[str, ...]:
        return tuple(option.label for option in self.sort_options)

    def numeric_key_for_label(self, label: str) -> str | None:
        for option in self.numeric_options:
            if option.label == label:
                return option.key
        return None

    def string_key_for_label(self, label: str) -> str | None:
        for option in self.string_options:
            if option.label == label:
                return option.key
        return None

    def sort_key_for_label(self, label: str) -> str | None:
        for option in self.sort_options:
            if option.label == label:
                return option.key
        return None

    def default_sort_label(self) -> str:
        for option in self.sort_options:
            if option.key == self.default_sort_key:
                return option.label
        return self.sort_options[0].label


@dataclass
class NumericFilterRowState:
    frame: tk.Frame
    field_var: tk.StringVar
    operator_var: tk.StringVar
    value_var: tk.StringVar


@dataclass
class StringFilterRowState:
    frame: tk.Frame
    field_var: tk.StringVar
    value_var: tk.StringVar


def format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return format_number(float(value))
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(part for part in (format_scalar(entry) for entry in value) if part)
    return str(value)


def coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_text(value: Any) -> str:
    text = str(value or "").casefold()
    collapsed = "".join(char if char.isalnum() else " " for char in text)
    return " ".join(collapsed.split())


def title_case(value: str) -> str:
    return value.replace("_", " ").title()


def prettify_identifier(value: str) -> str:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", value.replace("_", " "))
    spaced = spaced.replace("Ids", "IDs").replace("Id", "ID")
    return " ".join(spaced.split()).title()


def humanize_key(key: str) -> str:
    if key in OVERRIDE_LABELS:
        return OVERRIDE_LABELS[key]
    skill_req = SKILL_REQ_PATTERN.match(key)
    if skill_req:
        return f"{SKILL_LABELS[skill_req.group('skill')]} Requirement"
    if key in SKILL_LABELS:
        return SKILL_LABELS[key]
    spell_match = SPELL_COST_PATTERN.match(key)
    if spell_match:
        slot = spell_match.group("slot")
        body = "%" if spell_match.group("body") == "Pct" else "Raw"
        suffix = " Final" if spell_match.group("final") else ""
        return f"Spell {slot} Cost {body}{suffix}"
    element_match = ELEMENT_STAT_PATTERN.match(key)
    if element_match:
        element_label = ELEMENT_LABELS[element_match.group("element")]
        body_label = {
            "Dam": "Damage",
            "Def": "Defense",
            "Md": "Main Attack",
            "Sd": "Spell",
        }[element_match.group("body")]
        suffix = {
            None: "",
            "Pct": " %",
            "Raw": " Raw",
        }[element_match.group("suffix")]
        return f"{element_label} {body_label}{suffix}"
    return prettify_identifier(key)


def has_display_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return abs(float(value)) > 1e-9
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return any(has_display_value(entry) for entry in value)
    if isinstance(value, dict):
        return any(has_display_value(entry) for entry in value.values())
    return True


def parse_range_average(value: Any) -> float | None:
    match = RANGE_PATTERN.match(str(value or "").strip())
    if not match:
        return None
    return (float(match.group(1)) + float(match.group(2))) / 2.0


def make_section(title: str, rows: list[DisplayRow]) -> DisplaySection | None:
    if not rows:
        return None
    return DisplaySection(title=title, rows=tuple(rows))


def add_numeric_stat(registry: dict[str, str], target: dict[str, float], key: str, label: str, value: Any) -> None:
    number = coerce_number(value)
    if number is None:
        return
    registry.setdefault(key, label)
    target[key] = number


def add_string_stat(
    registry: dict[str, str],
    target: dict[str, tuple[str, ...]],
    key: str,
    label: str,
    value: Any,
) -> None:
    if value is None:
        return
    if isinstance(value, (list, tuple)):
        values = tuple(str(entry) for entry in value if str(entry).strip())
    else:
        text = str(value).strip()
        values = (text,) if text else ()
    if not values:
        return
    registry.setdefault(key, label)
    target[key] = values


def record_search_blob(title: str, subtitle: str, sections: tuple[DisplaySection, ...]) -> str:
    parts = [title, subtitle]
    for section in sections:
        parts.append(section.title)
        for row in section.rows:
            parts.append(row.label)
            parts.append(row.value)
    return normalize_text(" ".join(parts))


def normalize_item_record(
    raw: dict[str, Any],
    numeric_registry: dict[str, str],
    string_registry: dict[str, str],
) -> FinderRecord:
    title = str(raw.get("displayName") or raw.get("name") or "Unnamed")
    item_type = str(raw.get("type") or "").casefold()
    rarity_tag = str(raw.get("tier") or "").casefold()

    numeric_stats: dict[str, float] = {}
    string_stats: dict[str, tuple[str, ...]] = {}
    overview_rows: list[DisplayRow] = []
    requirement_rows: list[DisplayRow] = []
    damage_rows: list[DisplayRow] = []
    stat_rows: list[DisplayRow] = []
    major_rows: list[DisplayRow] = []
    note_rows: list[DisplayRow] = []

    for key in ITEM_META_KEYS:
        value = raw.get(key)
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        overview_rows.append(DisplayRow(label, format_scalar(value)))
        add_string_stat(string_registry, string_stats, key, label, value)
        if key == "lvl":
            add_numeric_stat(numeric_registry, numeric_stats, "lvl", "Level", value)

    numeric_stats["__tier_rank__"] = ITEM_TIER_RANKS.get(rarity_tag, -1.0)

    for key in ITEM_REQUIREMENT_KEYS:
        value = raw.get(key)
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        requirement_rows.append(DisplayRow(label, format_scalar(value)))
        add_numeric_stat(numeric_registry, numeric_stats, key, label, value)

    for key in ITEM_DAMAGE_KEYS:
        value = raw.get(key)
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        damage_rows.append(DisplayRow(label, str(value)))
        average = parse_range_average(value)
        if average is not None:
            add_numeric_stat(numeric_registry, numeric_stats, f"{key}Avg", f"{label} Avg", average)

    for key, value in raw.items():
        if key in ITEM_INTERNAL_SKIP or key in ITEM_META_KEYS or key in ITEM_REQUIREMENT_KEYS or key in ITEM_DAMAGE_KEYS:
            continue
        if isinstance(value, (dict, list, tuple)):
            continue
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        stat_rows.append(DisplayRow(label, format_scalar(value)))
        add_numeric_stat(numeric_registry, numeric_stats, key, label, value)
        if coerce_number(value) is None:
            add_string_stat(string_registry, string_stats, key, label, value)

    major_ids = raw.get("majorIds") or []
    if isinstance(major_ids, (list, tuple)):
        values = [str(entry).strip() for entry in major_ids if str(entry).strip()]
        for entry in values:
            major_rows.append(DisplayRow("Major ID", entry))
        if values:
            add_string_stat(string_registry, string_stats, "majorIds", "Major IDs", values)

    lore = raw.get("lore")
    if isinstance(lore, str) and lore.strip():
        note_rows.append(DisplayRow("Lore", lore.strip()))
        add_string_stat(string_registry, string_stats, "lore", "Lore", lore.strip())

    subtitle_parts = [
        str(raw.get("tier") or ""),
        title_case(str(raw.get("type") or "")),
        f"Lvl {format_scalar(raw.get('lvl'))}" if has_display_value(raw.get("lvl")) else "",
    ]
    subtitle = " | ".join(part for part in subtitle_parts if part)

    sections = tuple(
        section
        for section in (
            make_section("Overview", overview_rows),
            make_section("Requirements", requirement_rows),
            make_section("Damage", damage_rows),
            make_section("Stats", sorted(stat_rows, key=lambda row: normalize_text(row.label))),
            make_section("Major IDs", major_rows),
            make_section("Notes", note_rows),
        )
        if section is not None
    )

    add_string_stat(string_registry, string_stats, "name", "Name", title)

    return FinderRecord(
        dataset="items",
        title=title,
        subtitle=subtitle,
        type_tags=(item_type,) if item_type else (),
        rarity_tag=rarity_tag,
        numeric_stats=numeric_stats,
        string_stats=string_stats,
        sections=sections,
        search_blob=record_search_blob(title, subtitle, sections),
    )


def normalize_ingredient_record(
    raw: dict[str, Any],
    numeric_registry: dict[str, str],
    string_registry: dict[str, str],
) -> FinderRecord:
    title = str(raw.get("displayName") or raw.get("name") or "Unnamed")
    skills = tuple(str(skill).casefold() for skill in raw.get("skills", []) if str(skill).strip())
    rarity_tag = str(raw.get("tier") or "")

    numeric_stats: dict[str, float] = {}
    string_stats: dict[str, tuple[str, ...]] = {}
    overview_rows: list[DisplayRow] = []
    item_id_rows: list[DisplayRow] = []
    consumable_rows: list[DisplayRow] = []
    position_rows: list[DisplayRow] = []
    roll_rows: list[DisplayRow] = []

    if has_display_value(raw.get("lvl")):
        overview_rows.append(DisplayRow("Level", format_scalar(raw.get("lvl"))))
        add_numeric_stat(numeric_registry, numeric_stats, "lvl", "Level", raw.get("lvl"))
    if has_display_value(raw.get("tier")):
        overview_rows.append(DisplayRow("Stars", format_scalar(raw.get("tier"))))
        add_numeric_stat(numeric_registry, numeric_stats, "__stars__", "Stars", raw.get("tier"))
    if skills:
        pretty_skills = ", ".join(title_case(skill) for skill in skills)
        overview_rows.append(DisplayRow("Types", pretty_skills))
        add_string_stat(string_registry, string_stats, "skills", "Types", pretty_skills)

    add_string_stat(string_registry, string_stats, "name", "Name", title)

    for key, value in sorted((raw.get("itemIDs") or {}).items(), key=lambda entry: entry[0].casefold()):
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        item_id_rows.append(DisplayRow(label, format_scalar(value)))
        add_numeric_stat(numeric_registry, numeric_stats, f"item.{key}", f"Item {label}", value)

    for key, value in sorted((raw.get("consumableIDs") or {}).items(), key=lambda entry: entry[0].casefold()):
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        consumable_rows.append(DisplayRow(label, format_scalar(value)))
        add_numeric_stat(numeric_registry, numeric_stats, f"consumable.{key}", f"Consumable {label}", value)

    for key, value in sorted((raw.get("posMods") or {}).items(), key=lambda entry: entry[0].casefold()):
        if not has_display_value(value):
            continue
        label = humanize_key(key)
        position_rows.append(DisplayRow(label, format_scalar(value)))
        add_numeric_stat(numeric_registry, numeric_stats, f"position.{key}", f"Position {label}", value)

    for key, bounds in sorted((raw.get("ids") or {}).items(), key=lambda entry: entry[0].casefold()):
        if not isinstance(bounds, dict):
            continue
        minimum = bounds.get("minimum", 0)
        maximum = bounds.get("maximum", 0)
        if not has_display_value(minimum) and not has_display_value(maximum):
            continue
        label = humanize_key(key)
        roll_rows.append(DisplayRow(label, f"{format_scalar(minimum)} to {format_scalar(maximum)}"))
        add_numeric_stat(numeric_registry, numeric_stats, f"roll.{key}.min", f"{label} Min", minimum)
        add_numeric_stat(numeric_registry, numeric_stats, f"roll.{key}.max", f"{label} Max", maximum)

    subtitle_parts = [
        f"Stars {format_scalar(raw.get('tier'))}" if has_display_value(raw.get("tier")) else "",
        f"Lvl {format_scalar(raw.get('lvl'))}" if has_display_value(raw.get("lvl")) else "",
        ", ".join(title_case(skill) for skill in skills) if skills else "",
    ]
    subtitle = " | ".join(part for part in subtitle_parts if part)

    sections = tuple(
        section
        for section in (
            make_section("Overview", overview_rows),
            make_section("Item IDs", item_id_rows),
            make_section("Consumable IDs", consumable_rows),
            make_section("Position Modifiers", position_rows),
            make_section("Rolls", roll_rows),
        )
        if section is not None
    )

    return FinderRecord(
        dataset="ingredients",
        title=title,
        subtitle=subtitle,
        type_tags=skills,
        rarity_tag=rarity_tag,
        numeric_stats=numeric_stats,
        string_stats=string_stats,
        sections=sections,
        search_blob=record_search_blob(title, subtitle, sections),
    )


def sorted_stat_options(registry: dict[str, str]) -> tuple[StatOption, ...]:
    return tuple(
        StatOption(key=key, label=label)
        for key, label in sorted(registry.items(), key=lambda entry: normalize_text(entry[1]))
        if not key.startswith("__")
    )


def unique_sort_options(primary: list[StatOption], extra: list[StatOption]) -> tuple[StatOption, ...]:
    seen: set[str] = set()
    combined: list[StatOption] = []
    for option in [*primary, *extra]:
        if option.label in seen:
            continue
        seen.add(option.label)
        combined.append(option)
    return tuple(combined)


def load_item_bundle() -> DatasetBundle:
    payload = json.loads(ITEM_DATA_PATH.read_text(encoding="utf-8"))
    numeric_registry: dict[str, str] = {}
    string_registry: dict[str, str] = {}
    records = [normalize_item_record(raw, numeric_registry, string_registry) for raw in payload["items"]]
    numeric_options = sorted_stat_options(numeric_registry)
    string_options = tuple(
        StatOption(key=key, label=label)
        for key, label in sorted(string_registry.items(), key=lambda entry: normalize_text(entry[1]))
        if key != "name"
    )
    sort_options = unique_sort_options(
        [
            StatOption("__name__", "Name"),
            StatOption("lvl", "Level"),
            StatOption("__tier_rank__", "Rarity"),
        ],
        list(numeric_options),
    )
    return DatasetBundle(
        key="items",
        heading="Advanced Item Search",
        type_label="Type",
        type_options=ITEM_TYPE_OPTIONS,
        rarity_label="Rarity",
        rarity_options=ITEM_RARITY_OPTIONS,
        records=records,
        numeric_options=numeric_options,
        string_options=string_options,
        sort_options=sort_options,
        default_sort_key="lvl",
    )


def load_ingredient_bundle() -> DatasetBundle:
    payload = json.loads(INGREDIENT_DATA_PATH.read_text(encoding="utf-8"))
    numeric_registry: dict[str, str] = {}
    string_registry: dict[str, str] = {}
    records = [normalize_ingredient_record(raw, numeric_registry, string_registry) for raw in payload]
    numeric_options = sorted_stat_options(numeric_registry)
    sort_options = unique_sort_options(
        [
            StatOption("__name__", "Name"),
            StatOption("lvl", "Level"),
            StatOption("__stars__", "Stars"),
        ],
        list(numeric_options),
    )
    return DatasetBundle(
        key="ingredients",
        heading="Advanced Ingredient Search",
        type_label="Types",
        type_options=INGREDIENT_TYPE_OPTIONS,
        rarity_label="Stars",
        rarity_options=INGREDIENT_STAR_OPTIONS,
        records=records,
        numeric_options=numeric_options,
        string_options=tuple(),
        sort_options=sort_options,
        default_sort_key="lvl",
    )


def compare_numeric(left: float, operator_text: str, right: float) -> bool:
    if operator_text == ">=":
        return left >= right
    if operator_text == ">":
        return left > right
    if operator_text == "=":
        return abs(left - right) < 1e-9
    if operator_text == "<=":
        return left <= right
    return left < right


def matches_string_filter(record: FinderRecord, key: str, value: str) -> bool:
    target = normalize_text(value)
    if not target:
        return True
    if key == "name":
        return target in normalize_text(record.title)
    values = record.string_stats.get(key, ())
    return any(target in normalize_text(entry) for entry in values)


def apply_record_filters(
    bundle: DatasetBundle,
    *,
    name_query: str,
    selected_types: set[str],
    selected_rarities: set[str],
    include_filters: list[tuple[str, str, float]],
    exclude_filters: list[tuple[str, str, float]],
    string_filters: list[tuple[str, str]],
) -> list[FinderRecord]:
    target_name = normalize_text(name_query)
    results: list[FinderRecord] = []

    for record in bundle.records:
        if target_name and target_name not in normalize_text(record.title):
            continue
        if selected_types and not any(tag in selected_types for tag in record.type_tags):
            continue
        if selected_rarities and record.rarity_tag not in selected_rarities:
            continue
        if any(not compare_numeric(record.numeric_stats.get(key, 0.0), op, value) for key, op, value in include_filters):
            continue
        if any(compare_numeric(record.numeric_stats.get(key, 0.0), op, value) for key, op, value in exclude_filters):
            continue
        if not all(matches_string_filter(record, key, value) for key, value in string_filters):
            continue
        results.append(record)

    return results


def sort_records(records: list[FinderRecord], sort_key: str, descending: bool) -> list[FinderRecord]:
    if sort_key == "__name__":
        return sorted(records, key=lambda record: normalize_text(record.title), reverse=descending)
    present = [record for record in records if sort_key in record.numeric_stats]
    missing = [record for record in records if sort_key not in record.numeric_stats]
    present_sorted = sorted(
        present,
        key=lambda record: (record.numeric_stats.get(sort_key, 0.0), normalize_text(record.title)),
        reverse=descending,
    )
    missing_sorted = sorted(missing, key=lambda record: normalize_text(record.title))
    return [*present_sorted, *missing_sorted]


def run_self_test() -> int:
    item_bundle = load_item_bundle()
    ingredient_bundle = load_ingredient_bundle()
    assert item_bundle.records
    assert ingredient_bundle.records
    assert apply_record_filters(
        item_bundle,
        name_query="Alstroemania",
        selected_types={"leggings"},
        selected_rarities={"legendary"},
        include_filters=[("lvl", ">=", 100.0)],
        exclude_filters=[],
        string_filters=[],
    )
    assert apply_record_filters(
        ingredient_bundle,
        name_query="Powders",
        selected_types={"jeweling"},
        selected_rarities={"2"},
        include_filters=[("lvl", ">=", 100.0)],
        exclude_filters=[],
        string_filters=[],
    )
    assert sort_records(item_bundle.records[:50], "lvl", True)
    print("Loaded items:", len(item_bundle.records))
    print("Loaded ingredients:", len(ingredient_bundle.records))
    print("Self-test passed.")
    return 0


class ItemFinderApp(tk.Tk):
    def __init__(self, item_bundle: DatasetBundle, ingredient_bundle: DatasetBundle) -> None:
        super().__init__()
        self.bundles = {
            item_bundle.key: item_bundle,
            ingredient_bundle.key: ingredient_bundle,
        }
        self.filtered_records: list[FinderRecord] = []
        self.visible_limit = INITIAL_RESULT_LIMIT
        self._card_value_labels: list[tk.Label] = []

        self.dataset_var = tk.StringVar(value="items")
        self.heading_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.sort_field_var = tk.StringVar()
        self.sort_order_var = tk.StringVar(value=SORT_ORDERS[0])
        self.status_var = tk.StringVar(value="Ready.")

        self.type_vars: dict[str, tk.BooleanVar] = {}
        self.rarity_vars: dict[str, tk.BooleanVar] = {}
        self.include_rows: list[NumericFilterRowState] = []
        self.exclude_rows: list[NumericFilterRowState] = []
        self.string_rows: list[StringFilterRowState] = []

        self.filter_section_frame: tk.Frame | None = None
        self.include_rows_frame: tk.Frame | None = None
        self.exclude_rows_frame: tk.Frame | None = None
        self.string_rows_frame: tk.Frame | None = None
        self.show_more_button: ttk.Button | None = None

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1180, 720)
        self.configure(bg=THEME["page_bg"])

        self._configure_style()
        self._build_ui()
        self._rebuild_dataset_controls()
        self.apply_filters(reset_scroll=True)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", padding=4)
        style.configure("TButton", padding=(8, 6))
        style.configure("TRadiobutton", background=THEME["page_bg"], foreground=THEME["text"])

    def active_bundle(self) -> DatasetBundle:
        return self.bundles[self.dataset_var.get()]

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=THEME["page_bg"], padx=18, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(2, weight=1)

        tk.Label(
            header,
            text="ItemFinder",
            bg=THEME["page_bg"],
            fg=THEME["text"],
            font=("Segoe UI", 22, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header,
            text="Local Wynnbuilder-style item and ingredient browser",
            bg=THEME["page_bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        toggle_frame = tk.Frame(header, bg=THEME["page_bg"])
        toggle_frame.grid(row=0, column=1, rowspan=2, sticky="w", padx=(28, 0))
        ttk.Radiobutton(toggle_frame, text="Items", value="items", variable=self.dataset_var, command=self._on_dataset_changed).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(toggle_frame, text="Ingredients", value="ingredients", variable=self.dataset_var, command=self._on_dataset_changed).grid(row=0, column=1, sticky="w")

        body = tk.Frame(self, bg=THEME["page_bg"], padx=18, pady=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        search_panel = tk.Frame(body, bg=THEME["panel_bg"], highlightbackground=THEME["line"], highlightthickness=1, padx=18, pady=16)
        search_panel.grid(row=0, column=0, sticky="ew")
        search_panel.columnconfigure(0, weight=1)

        tk.Label(search_panel, textvariable=self.heading_var, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 16, "bold"), anchor="w").grid(row=0, column=0, sticky="w")

        self.filter_section_frame = tk.Frame(search_panel, bg=THEME["panel_bg"])
        self.filter_section_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.filter_section_frame.columnconfigure(0, weight=1)

        result_header = tk.Frame(body, bg=THEME["page_bg"])
        result_header.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        result_header.columnconfigure(0, weight=1)
        tk.Label(result_header, textvariable=self.status_var, bg=THEME["page_bg"], fg=THEME["text"], font=("Segoe UI", 10), anchor="w").grid(row=0, column=0, sticky="w")

        self.show_more_button = ttk.Button(result_header, text=f"Show {RESULT_BATCH_SIZE} More", command=self.show_more)
        self.show_more_button.grid(row=0, column=1, sticky="e")

        results_shell = tk.Frame(body, bg=THEME["panel_alt"], highlightbackground=THEME["line"], highlightthickness=1)
        results_shell.grid(row=2, column=0, sticky="nsew")
        results_shell.columnconfigure(0, weight=1)
        results_shell.rowconfigure(0, weight=1)

        self.results_canvas = tk.Canvas(results_shell, bg=THEME["panel_alt"], highlightthickness=0, borderwidth=0)
        self.results_canvas.grid(row=0, column=0, sticky="nsew")
        results_scrollbar = ttk.Scrollbar(results_shell, orient=tk.VERTICAL, command=self.results_canvas.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_canvas.configure(yscrollcommand=results_scrollbar.set)

        self.cards_frame = tk.Frame(self.results_canvas, bg=THEME["panel_alt"], padx=14, pady=14)
        self._cards_window = self.results_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.bind("<Configure>", self._update_scrollregion, add="+")
        self.results_canvas.bind("<Configure>", self._sync_canvas_width, add="+")
        self.results_canvas.bind("<Enter>", self._bind_mousewheel, add="+")
        self.results_canvas.bind("<Leave>", self._unbind_mousewheel, add="+")

    def _on_dataset_changed(self) -> None:
        self.name_var.set("")
        self.sort_order_var.set(SORT_ORDERS[0])
        self._rebuild_dataset_controls()
        self.apply_filters(reset_scroll=True)

    def _build_field_block(self, parent: tk.Misc, label_text: str) -> tk.Frame:
        block = tk.Frame(parent, bg=THEME["panel_bg"])
        block.columnconfigure(0, weight=1)
        tk.Label(block, text=label_text, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 6))
        return block

    def _build_filter_group(self, parent: tk.Misc, label_text: str) -> tk.Frame:
        block = tk.Frame(parent, bg=THEME["panel_bg"])
        block.columnconfigure(0, weight=1)
        tk.Label(block, text=label_text, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 6))
        return block

    def _build_toggle_block(
        self,
        parent: tk.Misc,
        label_text: str,
        options: tuple[tuple[str, str], ...],
        variable_target: dict[str, tk.BooleanVar],
        select_all: Any,
        clear_all: Any,
    ) -> tk.Frame:
        block = tk.Frame(parent, bg=THEME["panel_bg"])
        block.columnconfigure(0, weight=1)

        label_row = tk.Frame(block, bg=THEME["panel_bg"])
        label_row.grid(row=0, column=0, sticky="ew")
        label_row.columnconfigure(0, weight=1)
        tk.Label(label_row, text=label_text, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ttk.Button(label_row, text="All", command=select_all).grid(row=0, column=1, sticky="e")
        ttk.Button(label_row, text="None", command=clear_all).grid(row=0, column=2, sticky="e", padx=(4, 0))

        options_frame = tk.Frame(block, bg=THEME["panel_bg"])
        options_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        for index, (label, key) in enumerate(options):
            variable = tk.BooleanVar(value=True)
            variable_target[key] = variable
            toggle = tk.Checkbutton(
                options_frame,
                text=label,
                variable=variable,
                indicatoron=False,
                padx=10,
                pady=5,
                bg=THEME["button_bg"],
                activebackground=THEME["button_active"],
                fg=THEME["text"],
                selectcolor=THEME["accent_soft"],
                relief=tk.RIDGE,
                bd=1,
                font=("Segoe UI", 9),
            )
            toggle.grid(row=index // 8, column=index % 8, sticky="w", padx=(0, 6), pady=(0, 6))

        return block

    def _rebuild_dataset_controls(self) -> None:
        bundle = self.active_bundle()
        self.heading_var.set(bundle.heading)

        for child in self.filter_section_frame.winfo_children():
            child.destroy()

        self.type_vars.clear()
        self.rarity_vars.clear()
        self.include_rows.clear()
        self.exclude_rows.clear()
        self.string_rows.clear()

        name_frame = self._build_field_block(self.filter_section_frame, "Name:")
        name_frame.grid(row=0, column=0, sticky="ew")
        name_frame.columnconfigure(0, weight=1)
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=0, sticky="ew")
        name_entry.bind("<Return>", lambda _event: self.apply_filters(reset_scroll=True), add="+")

        type_frame = self._build_toggle_block(self.filter_section_frame, f"{bundle.type_label}:", bundle.type_options, self.type_vars, self._select_all_types, self._clear_all_types)
        type_frame.grid(row=1, column=0, sticky="ew", pady=(14, 0))

        rarity_frame = self._build_toggle_block(self.filter_section_frame, f"{bundle.rarity_label}:", bundle.rarity_options, self.rarity_vars, self._select_all_rarities, self._clear_all_rarities)
        rarity_frame.grid(row=2, column=0, sticky="ew", pady=(14, 0))

        include_frame = self._build_filter_group(self.filter_section_frame, "Filters:")
        include_frame.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        self.include_rows_frame = tk.Frame(include_frame, bg=THEME["panel_bg"])
        self.include_rows_frame.grid(row=1, column=0, sticky="ew")
        self._add_numeric_filter_row(self.include_rows, self.include_rows_frame)
        ttk.Button(include_frame, text="+ Add Filter", command=lambda: self._add_numeric_filter_row(self.include_rows, self.include_rows_frame)).grid(row=2, column=0, sticky="w", pady=(8, 0))

        exclude_frame = self._build_filter_group(self.filter_section_frame, "Excluded Filters:")
        exclude_frame.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        self.exclude_rows_frame = tk.Frame(exclude_frame, bg=THEME["panel_bg"])
        self.exclude_rows_frame.grid(row=1, column=0, sticky="ew")
        self._add_numeric_filter_row(self.exclude_rows, self.exclude_rows_frame)
        ttk.Button(exclude_frame, text="+ Add Excluded Filter", command=lambda: self._add_numeric_filter_row(self.exclude_rows, self.exclude_rows_frame)).grid(row=2, column=0, sticky="w", pady=(8, 0))

        next_row = 5
        if bundle.string_options:
            string_frame = self._build_filter_group(self.filter_section_frame, "String Filters:")
            string_frame.grid(row=5, column=0, sticky="ew", pady=(14, 0))
            self.string_rows_frame = tk.Frame(string_frame, bg=THEME["panel_bg"])
            self.string_rows_frame.grid(row=1, column=0, sticky="ew")
            self._add_string_filter_row()
            ttk.Button(string_frame, text="+ Add String Filter", command=self._add_string_filter_row).grid(row=2, column=0, sticky="w", pady=(8, 0))
            next_row = 6
        else:
            self.string_rows_frame = None

        sort_frame = self._build_field_block(self.filter_section_frame, "Sort By:")
        sort_frame.grid(row=next_row, column=0, sticky="ew", pady=(14, 0))
        sort_frame.columnconfigure(0, weight=1)

        self.sort_field_var.set(bundle.default_sort_label())
        ttk.Combobox(sort_frame, textvariable=self.sort_field_var, values=bundle.sort_labels, width=34).grid(row=0, column=0, sticky="ew")
        ttk.Combobox(sort_frame, textvariable=self.sort_order_var, values=SORT_ORDERS, state="readonly", width=14).grid(row=0, column=1, sticky="e", padx=(10, 0))

        button_frame = tk.Frame(self.filter_section_frame, bg=THEME["panel_bg"])
        button_frame.grid(row=next_row + 1, column=0, sticky="w", pady=(16, 0))
        ttk.Button(button_frame, text="Search!", command=lambda: self.apply_filters(reset_scroll=True)).grid(row=0, column=0, sticky="w")
        ttk.Button(button_frame, text="Reset", command=self._reset_current_dataset).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._select_all_types()
        self._select_all_rarities()

    def _add_numeric_filter_row(self, store: list[NumericFilterRowState], parent: tk.Frame) -> None:
        bundle = self.active_bundle()
        frame = tk.Frame(parent, bg=THEME["panel_bg"])
        frame.grid(row=len(store), column=0, sticky="ew", pady=(0, 6))
        frame.columnconfigure(0, weight=1)

        field_var = tk.StringVar()
        operator_var = tk.StringVar(value=">=")
        value_var = tk.StringVar()

        ttk.Combobox(frame, textvariable=field_var, values=("", *bundle.numeric_labels), width=36).grid(row=0, column=0, sticky="ew")
        ttk.Combobox(frame, textvariable=operator_var, values=NUMERIC_OPERATORS, state="readonly", width=5).grid(row=0, column=1, sticky="w", padx=(8, 8))
        value_entry = ttk.Entry(frame, textvariable=value_var, width=14)
        value_entry.grid(row=0, column=2, sticky="w")

        row_state = NumericFilterRowState(frame=frame, field_var=field_var, operator_var=operator_var, value_var=value_var)
        value_entry.bind("<Return>", lambda _event: self.apply_filters(reset_scroll=True), add="+")
        ttk.Button(frame, text="x", width=3, command=lambda: self._remove_numeric_filter_row(store, row_state)).grid(row=0, column=3, sticky="e", padx=(8, 0))
        store.append(row_state)

    def _remove_numeric_filter_row(self, store: list[NumericFilterRowState], state: NumericFilterRowState) -> None:
        if len(store) == 1:
            state.field_var.set("")
            state.operator_var.set(">=")
            state.value_var.set("")
            return
        store.remove(state)
        state.frame.destroy()
        for index, row in enumerate(store):
            row.frame.grid_configure(row=index)

    def _add_string_filter_row(self) -> None:
        bundle = self.active_bundle()
        frame = tk.Frame(self.string_rows_frame, bg=THEME["panel_bg"])
        frame.grid(row=len(self.string_rows), column=0, sticky="ew", pady=(0, 6))
        frame.columnconfigure(0, weight=1)

        field_var = tk.StringVar()
        value_var = tk.StringVar()
        ttk.Combobox(frame, textvariable=field_var, values=("", *bundle.string_labels), width=30).grid(row=0, column=0, sticky="ew")
        value_entry = ttk.Entry(frame, textvariable=value_var, width=32)
        value_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))

        row_state = StringFilterRowState(frame=frame, field_var=field_var, value_var=value_var)
        value_entry.bind("<Return>", lambda _event: self.apply_filters(reset_scroll=True), add="+")
        ttk.Button(frame, text="x", width=3, command=lambda: self._remove_string_filter_row(row_state)).grid(row=0, column=2, sticky="e")
        self.string_rows.append(row_state)

    def _remove_string_filter_row(self, state: StringFilterRowState) -> None:
        if len(self.string_rows) == 1:
            state.field_var.set("")
            state.value_var.set("")
            return
        self.string_rows.remove(state)
        state.frame.destroy()
        for index, row in enumerate(self.string_rows):
            row.frame.grid_configure(row=index)

    def _select_all_types(self) -> None:
        for variable in self.type_vars.values():
            variable.set(True)

    def _clear_all_types(self) -> None:
        for variable in self.type_vars.values():
            variable.set(False)

    def _select_all_rarities(self) -> None:
        for variable in self.rarity_vars.values():
            variable.set(True)

    def _clear_all_rarities(self) -> None:
        for variable in self.rarity_vars.values():
            variable.set(False)

    def _reset_current_dataset(self) -> None:
        self.name_var.set("")
        self.sort_order_var.set(SORT_ORDERS[0])
        self._rebuild_dataset_controls()
        self.apply_filters(reset_scroll=True)

    def _collect_numeric_filters(self, rows: list[NumericFilterRowState]) -> tuple[list[tuple[str, str, float]], str | None]:
        bundle = self.active_bundle()
        filters: list[tuple[str, str, float]] = []
        for row in rows:
            label = row.field_var.get().strip()
            operator_text = row.operator_var.get().strip() or ">="
            value_text = row.value_var.get().strip()
            if not label and not value_text:
                continue
            stat_key = bundle.numeric_key_for_label(label)
            if stat_key is None:
                return [], f"Unknown numeric filter: {label}"
            threshold = coerce_number(value_text)
            if threshold is None:
                return [], f"Invalid numeric value for {label}: {value_text}"
            filters.append((stat_key, operator_text, threshold))
        return filters, None

    def _collect_string_filters(self) -> tuple[list[tuple[str, str]], str | None]:
        bundle = self.active_bundle()
        filters: list[tuple[str, str]] = []
        for row in self.string_rows:
            label = row.field_var.get().strip()
            value_text = row.value_var.get().strip()
            if not label and not value_text:
                continue
            stat_key = bundle.string_key_for_label(label)
            if stat_key is None:
                return [], f"Unknown string filter: {label}"
            filters.append((stat_key, value_text))
        return filters, None

    def apply_filters(self, reset_scroll: bool) -> None:
        bundle = self.active_bundle()
        include_filters, error_text = self._collect_numeric_filters(self.include_rows)
        if error_text:
            self.status_var.set(error_text)
            return

        exclude_filters, error_text = self._collect_numeric_filters(self.exclude_rows)
        if error_text:
            self.status_var.set(error_text)
            return

        string_filters, error_text = self._collect_string_filters()
        if error_text:
            self.status_var.set(error_text)
            return

        sort_key = bundle.sort_key_for_label(self.sort_field_var.get().strip())
        if sort_key is None:
            self.status_var.set(f"Unknown sort field: {self.sort_field_var.get().strip()}")
            return

        selected_types = {key for key, variable in self.type_vars.items() if variable.get()}
        selected_rarities = {key for key, variable in self.rarity_vars.items() if variable.get()}
        if not selected_types:
            self.filtered_records = []
            self.status_var.set(f"No {bundle.type_label.lower()} selected.")
            self.render_results(reset_scroll=reset_scroll)
            return
        if not selected_rarities:
            self.filtered_records = []
            self.status_var.set(f"No {bundle.rarity_label.lower()} selected.")
            self.render_results(reset_scroll=reset_scroll)
            return

        self.filtered_records = sort_records(
            apply_record_filters(
                bundle,
                name_query=self.name_var.get().strip(),
                selected_types=selected_types,
                selected_rarities=selected_rarities,
                include_filters=include_filters,
                exclude_filters=exclude_filters,
                string_filters=string_filters,
            ),
            sort_key=sort_key,
            descending=self.sort_order_var.get() == "Descending",
        )
        self.visible_limit = INITIAL_RESULT_LIMIT
        self.render_results(reset_scroll=reset_scroll)

    def show_more(self) -> None:
        self.visible_limit += RESULT_BATCH_SIZE
        self.render_results(reset_scroll=False)

    def render_results(self, reset_scroll: bool) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()
        self._card_value_labels.clear()

        visible = self.filtered_records[: self.visible_limit]
        if not visible:
            empty = tk.Frame(self.cards_frame, bg=THEME["panel_bg"], highlightbackground=THEME["line"], highlightthickness=1, padx=18, pady=18)
            empty.grid(row=0, column=0, sticky="ew")
            tk.Label(
                empty,
                text="No matches. Adjust the selected types, rarity/stars, or stat filters and try again.",
                bg=THEME["panel_bg"],
                fg=THEME["text"],
                font=("Segoe UI", 11),
                anchor="w",
                justify="left",
                wraplength=1280,
            ).pack(fill=tk.X)
        else:
            for index, record in enumerate(visible):
                self._render_card(index, record)

        dataset_name = "ingredients" if self.dataset_var.get() == "ingredients" else "items"
        hidden = max(0, len(self.filtered_records) - len(visible))
        if hidden:
            self.status_var.set(f"Showing {len(visible):,} of {len(self.filtered_records):,} matching {dataset_name}.")
            self.show_more_button.grid()
        else:
            self.status_var.set(f"Showing {len(visible):,} matching {dataset_name}.")
            self.show_more_button.grid_remove()

        self.update_idletasks()
        self._update_scrollregion()
        if reset_scroll:
            self.results_canvas.yview_moveto(0.0)

    def _render_card(self, row: int, record: FinderRecord) -> None:
        card = tk.Frame(self.cards_frame, bg=THEME["panel_bg"], highlightbackground=THEME["line"], highlightthickness=1, padx=16, pady=14)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.columnconfigure(0, weight=1)

        header = tk.Frame(card, bg=THEME["panel_bg"])
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        tk.Label(header, text=record.title, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 16, "bold"), anchor="w", justify="left").grid(row=0, column=0, sticky="w")
        if record.subtitle:
            tk.Label(header, text=record.subtitle, bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 10), anchor="w", justify="left").grid(row=1, column=0, sticky="w", pady=(2, 0))

        sections_frame = tk.Frame(card, bg=THEME["panel_bg"])
        sections_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        sections_frame.columnconfigure(0, weight=1)

        for index, section in enumerate(record.sections):
            box = tk.Frame(sections_frame, bg=THEME["panel_alt"], highlightbackground=THEME["line_soft"], highlightthickness=1, padx=12, pady=10)
            box.grid(row=index, column=0, sticky="ew", pady=(0, 8))
            box.columnconfigure(1, weight=1)

            tk.Label(box, text=section.title, bg=THEME["panel_alt"], fg=THEME["accent"], font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
            for line_index, display_row in enumerate(section.rows, start=1):
                tk.Label(box, text=f"{display_row.label}:", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Segoe UI", 9, "bold"), anchor="nw", justify="left").grid(row=line_index, column=0, sticky="nw", padx=(0, 8), pady=(0, 4))
                value_label = tk.Label(
                    box,
                    text=display_row.value,
                    bg=THEME["panel_alt"],
                    fg=THEME["text"],
                    font=("Segoe UI", 9),
                    anchor="nw",
                    justify="left",
                    wraplength=1180,
                )
                value_label.grid(row=line_index, column=1, sticky="ew", pady=(0, 4))
                self._card_value_labels.append(value_label)

    def _bind_mousewheel(self, _event: tk.Event | None = None) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event | None = None) -> None:
        self.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.results_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _update_scrollregion(self, _event: tk.Event | None = None) -> None:
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

    def _sync_canvas_width(self, event: tk.Event) -> None:
        self.results_canvas.itemconfigure(self._cards_window, width=event.width)
        wraplength = max(480, event.width - 210)
        for label in self._card_value_labels:
            label.configure(wraplength=wraplength)


def main() -> int:
    parser = argparse.ArgumentParser(description="Browse WynnBuilder items and WynnCrafter ingredients in a Wynnbuilder-style search UI.")
    parser.add_argument("--self-test", action="store_true", help="Load the datasets and run a non-GUI smoke test.")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    app = ItemFinderApp(load_item_bundle(), load_ingredient_bundle())
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
