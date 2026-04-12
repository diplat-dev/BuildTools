from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
import multiprocessing as mp
import os
import queue
import random
import threading
import time
import tkinter as tk
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from tkinter import ttk
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "items_compress.json"

APP_TITLE = "Wynn Build Tester"
WINDOW_SIZE = "1440x900"
DETECTED_LOGICAL_CPUS = max(1, int(os.cpu_count() or 1))
DEFAULT_MCTS_WORKERS = max(1, DETECTED_LOGICAL_CPUS // 2)
DEFAULT_COMBAT_LEVEL_FALLBACK = 105
MAX_COMBAT_LEVEL_INPUT = 200

LIGHT_THEME = {
    "bg": "#f3f5f8",
    "fg": "#17212b",
    "muted": "#5b6673",
    "input_bg": "#ffffff",
    "button_bg": "#e6ebf2",
    "button_active": "#d9e1ec",
    "border": "#c7d1de",
    "accent": "#3e7cb1",
    "selection": "#3e7cb1",
    "selection_fg": "#ffffff",
}
DARK_THEME = {
    "bg": "#10161f",
    "fg": "#e8edf5",
    "muted": "#97a4b7",
    "input_bg": "#182331",
    "button_bg": "#243344",
    "button_active": "#31465c",
    "border": "#33475c",
    "accent": "#6fb1ff",
    "selection": "#34699c",
    "selection_fg": "#ffffff",
}

SKILLS = ("str", "dex", "int", "def", "agi")
SKILL_LABELS = {
    "str": "Strength",
    "dex": "Dexterity",
    "int": "Intelligence",
    "def": "Defense",
    "agi": "Agility",
}
REQ_KEYS = {
    "strReq": "str",
    "dexReq": "dex",
    "intReq": "int",
    "defReq": "def",
    "agiReq": "agi",
}
ELEMENT_ORDER = ("n", "e", "t", "w", "f", "a")
ELEMENT_LABELS = {
    "n": "Neutral",
    "e": "Earth",
    "t": "Thunder",
    "w": "Water",
    "f": "Fire",
    "a": "Air",
}
ELEMENT_TO_SKILL = {
    "e": "str",
    "t": "dex",
    "w": "int",
    "f": "def",
    "a": "agi",
}
WEAPON_CLASS_NAMES = {
    "bow": "Archer",
    "dagger": "Assassin",
    "relik": "Shaman",
    "spear": "Warrior",
    "wand": "Mage",
}
ATTACK_SPEED_MULTIPLIERS = {
    "SUPER_FAST": 4.30,
    "VERY_FAST": 3.10,
    "FAST": 2.50,
    "NORMAL": 2.05,
    "SLOW": 1.50,
    "VERY_SLOW": 0.83,
    "SUPER_SLOW": 0.51,
}
SLOT_CONFIGS = (
    ("Helmet", "helmet"),
    ("Chestplate", "chestplate"),
    ("Pants", "leggings"),
    ("Boots", "boots"),
    ("Ring 1", "ring"),
    ("Ring 2", "ring"),
    ("Bracelet", "bracelet"),
    ("Necklace", "necklace"),
    ("Weapon", "weapon"),
)
STRUCTURAL_KEYS = {
    "id",
    "name",
    "displayName",
    "category",
    "type",
    "armourMaterial",
    "drop",
    "dropInfo",
    "icon",
    "lore",
    "majorIds",
    "classReq",
    "restrict",
    "fixID",
    "allowCraftsman",
    "persistent",
    "tier",
    "atkSpd",
    "averageDps",
    "nDam",
    "eDam",
    "tDam",
    "wDam",
    "fDam",
    "aDam",
}
DISPLAY_STAT_ORDER = [
    "hp",
    "hpBonus",
    "hprRaw",
    "hprPct",
    "healPct",
    "aDef",
    "eDef",
    "tDef",
    "wDef",
    "fDef",
    "aDefPct",
    "eDefPct",
    "tDefPct",
    "wDefPct",
    "fDefPct",
    "rDefPct",
    "str",
    "dex",
    "int",
    "def",
    "agi",
    "mr",
    "ms",
    "ls",
    "lb",
    "lq",
    "eSteal",
    "xpb",
    "gXp",
    "gSpd",
    "expd",
    "maxMana",
    "spd",
    "sprint",
    "sprintReg",
    "jh",
    "atkTier",
    "mainAttackRange",
    "damPct",
    "damRaw",
    "mdPct",
    "mdRaw",
    "sdPct",
    "sdRaw",
    "critDamPct",
    "poison",
    "nDamPct",
    "eDamPct",
    "tDamPct",
    "wDamPct",
    "fDamPct",
    "aDamPct",
    "rDamPct",
    "nDamRaw",
    "eDamRaw",
    "tDamRaw",
    "wDamRaw",
    "fDamRaw",
    "aDamRaw",
    "rDamRaw",
    "nMdPct",
    "eMdPct",
    "tMdPct",
    "wMdPct",
    "fMdPct",
    "aMdPct",
    "rMdPct",
    "nMdRaw",
    "eMdRaw",
    "tMdRaw",
    "wMdRaw",
    "fMdRaw",
    "aMdRaw",
    "rMdRaw",
    "nSdPct",
    "eSdPct",
    "tSdPct",
    "wSdPct",
    "fSdPct",
    "aSdPct",
    "rSdPct",
    "nSdRaw",
    "eSdRaw",
    "tSdRaw",
    "wSdRaw",
    "fSdRaw",
    "aSdRaw",
    "rSdRaw",
    "spPct1",
    "spPct2",
    "spPct3",
    "spPct4",
    "spRaw1",
    "spRaw2",
    "spRaw3",
    "spRaw4",
    "kb",
    "slowEnemy",
    "weakenEnemy",
    "ref",
    "thorns",
]
STAT_LABELS = {
    "hp": "Health Bonus",
    "hpBonus": "Health Bonus (Weapon)",
    "hprRaw": "Health Regen Raw",
    "hprPct": "Health Regen %",
    "healPct": "Heal %",
    "aDef": "Air Defense",
    "eDef": "Earth Defense",
    "tDef": "Thunder Defense",
    "wDef": "Water Defense",
    "fDef": "Fire Defense",
    "aDefPct": "Air Defense %",
    "eDefPct": "Earth Defense %",
    "tDefPct": "Thunder Defense %",
    "wDefPct": "Water Defense %",
    "fDefPct": "Fire Defense %",
    "rDefPct": "Rainbow Defense %",
    "str": "Strength Bonus",
    "dex": "Dexterity Bonus",
    "int": "Intelligence Bonus",
    "def": "Defense Bonus",
    "agi": "Agility Bonus",
    "mr": "Mana Regen",
    "ms": "Mana Steal",
    "ls": "Life Steal",
    "lb": "Loot Bonus",
    "lq": "Loot Quality %",
    "eSteal": "Emerald Stealing",
    "xpb": "Combat XP Bonus %",
    "gXp": "Gathering XP Bonus %",
    "gSpd": "Gathering Speed %",
    "expd": "Exploding %",
    "maxMana": "Max Mana",
    "spd": "Walk Speed %",
    "sprint": "Sprint %",
    "sprintReg": "Sprint Regen %",
    "jh": "Jump Height",
    "atkTier": "Attack Speed Tier",
    "mainAttackRange": "Main Attack Range %",
    "damPct": "Damage %",
    "damRaw": "Raw Damage",
    "mdPct": "Main Attack Damage %",
    "mdRaw": "Raw Main Attack Damage",
    "sdPct": "Spell Damage %",
    "sdRaw": "Raw Spell Damage",
    "critDamPct": "Critical Damage %",
    "poison": "Poison",
    "nDamPct": "Neutral Damage %",
    "eDamPct": "Earth Damage %",
    "tDamPct": "Thunder Damage %",
    "wDamPct": "Water Damage %",
    "fDamPct": "Fire Damage %",
    "aDamPct": "Air Damage %",
    "rDamPct": "Rainbow Damage %",
    "nDamRaw": "Neutral Raw Damage",
    "eDamRaw": "Earth Raw Damage",
    "tDamRaw": "Thunder Raw Damage",
    "wDamRaw": "Water Raw Damage",
    "fDamRaw": "Fire Raw Damage",
    "aDamRaw": "Air Raw Damage",
    "rDamRaw": "Rainbow Raw Damage",
    "nMdPct": "Neutral Main Attack %",
    "eMdPct": "Earth Main Attack %",
    "tMdPct": "Thunder Main Attack %",
    "wMdPct": "Water Main Attack %",
    "fMdPct": "Fire Main Attack %",
    "aMdPct": "Air Main Attack %",
    "rMdPct": "Rainbow Main Attack %",
    "nMdRaw": "Neutral Raw Main Attack",
    "eMdRaw": "Earth Raw Main Attack",
    "tMdRaw": "Thunder Raw Main Attack",
    "wMdRaw": "Water Raw Main Attack",
    "fMdRaw": "Fire Raw Main Attack",
    "aMdRaw": "Air Raw Main Attack",
    "rMdRaw": "Rainbow Raw Main Attack",
    "nSdPct": "Neutral Spell %",
    "eSdPct": "Earth Spell %",
    "tSdPct": "Thunder Spell %",
    "wSdPct": "Water Spell %",
    "fSdPct": "Fire Spell %",
    "aSdPct": "Air Spell %",
    "rSdPct": "Rainbow Spell %",
    "nSdRaw": "Neutral Raw Spell",
    "eSdRaw": "Earth Raw Spell",
    "tSdRaw": "Thunder Raw Spell",
    "wSdRaw": "Water Raw Spell",
    "fSdRaw": "Fire Raw Spell",
    "aSdRaw": "Air Raw Spell",
    "rSdRaw": "Rainbow Raw Spell",
    "spPct1": "Spell 1 Cost %",
    "spPct2": "Spell 2 Cost %",
    "spPct3": "Spell 3 Cost %",
    "spPct4": "Spell 4 Cost %",
    "spRaw1": "Spell 1 Cost Raw",
    "spRaw2": "Spell 2 Cost Raw",
    "spRaw3": "Spell 3 Cost Raw",
    "spRaw4": "Spell 4 Cost Raw",
    "kb": "Knockback %",
    "slowEnemy": "Slow Enemy %",
    "weakenEnemy": "Weaken Enemy %",
    "ref": "Reflection %",
    "thorns": "Thorns %",
}
PSEUDO_MELEE_BASE = "__meleeBaseAvg"
PSEUDO_SPELL_BASE = "__spellBaseAvg"
DIRECT_METRIC_ALIASES = {
    "hp_total": "hp_total",
    "hp": "hp_total",
    "ehp": "effective_hp",
    "effective hp": "effective_hp",
    "effective_hp": "effective_hp",
    "hpr": "hprRaw",
    "health regen": "hprRaw",
    "mr": "mr",
    "ms": "ms",
    "ws": "spd",
    "walk_speed": "spd",
    "walk speed": "spd",
    "melee_avg": "melee_avg",
    "melee damage": "melee_avg",
    "spell_avg": "spell_avg",
    "spell damage": "spell_avg",
}
MELEE_RELEVANT_KEYS = {
    "damPct",
    "damRaw",
    "mdPct",
    "mdRaw",
    "critDamPct",
    "rDamPct",
    "rMdPct",
    "nDamPct",
    "eDamPct",
    "tDamPct",
    "wDamPct",
    "fDamPct",
    "aDamPct",
    "nMdPct",
    "eMdPct",
    "tMdPct",
    "wMdPct",
    "fMdPct",
    "aMdPct",
    "rDamRaw",
    "rMdRaw",
    "nDamRaw",
    "eDamRaw",
    "tDamRaw",
    "wDamRaw",
    "fDamRaw",
    "aDamRaw",
    "nMdRaw",
    "eMdRaw",
    "tMdRaw",
    "wMdRaw",
    "fMdRaw",
    "aMdRaw",
    PSEUDO_MELEE_BASE,
    *SKILLS,
}
SPELL_RELEVANT_KEYS = {
    "damPct",
    "damRaw",
    "sdPct",
    "sdRaw",
    "critDamPct",
    "rDamPct",
    "rSdPct",
    "nDamPct",
    "eDamPct",
    "tDamPct",
    "wDamPct",
    "fDamPct",
    "aDamPct",
    "nSdPct",
    "eSdPct",
    "tSdPct",
    "wSdPct",
    "fSdPct",
    "aSdPct",
    "rDamRaw",
    "rSdRaw",
    "nDamRaw",
    "eDamRaw",
    "tDamRaw",
    "wDamRaw",
    "fDamRaw",
    "aDamRaw",
    "nSdRaw",
    "eSdRaw",
    "tSdRaw",
    "wSdRaw",
    "fSdRaw",
    "aSdRaw",
    PSEUDO_SPELL_BASE,
    *SKILLS,
}
GROUP_CANDIDATE_CAPS = {
    "Weapon": 120,
    "Helmet": 90,
    "Chestplate": 90,
    "Pants": 90,
    "Boots": 90,
    "Bracelet": 70,
    "Necklace": 70,
    "Rings": 500,
}
MCTS_UNCAPPED_STATE_THRESHOLD = 500_000
SEARCH_MODE_OPTIONS = {
    "Exact (optimal, slower)": "exact",
    "MCTS (anytime, stoppable)": "mcts",
}
SEARCH_MODE_LABELS = tuple(SEARCH_MODE_OPTIONS)
CONSTRAINT_OPERATORS = (">", "<", "=")
LEVEL_105_TOTAL_SKILL_POINTS = 200
LEVEL_105_MAX_BASE_SKILL = 100
MANA_ALLOCATION_METRICS = {
    "mr",
    "ms",
    "maxMana",
    "spPct1",
    "spPct2",
    "spPct3",
    "spPct4",
    "spRaw1",
    "spRaw2",
    "spRaw3",
    "spRaw4",
}

SKILL_PERCENTAGE_TEXT = """
1 1.0 51 40.5 101 65.4
2 2.0 52 41.1 102 65.7
3 2.9 53 41.7 103 66.1
4 3.9 54 42.3 104 66.5
5 4.9 55 42.9 105 66.9
6 5.8 56 43.5 106 67.3
7 6.7 57 44.1 107 67.6
8 7.7 58 44.7 108 68.0
9 8.6 59 45.3 109 68.4
10 9.5 60 45.8 110 68.7
11 10.4 61 46.4 111 69.1
12 11.3 62 47.0 112 69.4
13 12.2 63 47.5 113 69.8
14 13.1 64 48.1 114 70.1
15 13.9 65 48.6 115 70.5
16 14.8 66 49.2 116 70.8
17 15.7 67 49.7 117 71.2
18 16.5 68 50.3 118 71.5
19 17.3 69 50.8 119 71.8
20 18.2 70 51.3 120 72.2
21 19.0 71 51.8 121 72.5
22 19.8 72 52.3 122 72.8
23 20.6 73 52.8 123 73.1
24 21.4 74 53.4 124 73.5
25 22.2 75 53.9 125 73.8
26 23.0 76 54.3 126 74.1
27 23.8 77 54.8 127 74.4
28 24.6 78 55.3 128 74.7
29 25.3 79 55.8 129 75.0
30 26.1 80 56.3 130 75.3
31 26.8 81 56.8 131 75.6
32 27.6 82 57.2 132 75.9
33 28.3 83 57.7 133 76.2
34 29.0 84 58.1 134 76.5
35 29.8 85 58.6 135 76.8
36 30.5 86 59.1 136 77.1
37 31.2 87 59.5 137 77.3
38 31.9 88 59.9 138 77.6
39 32.6 89 60.4 139 77.9
40 33.3 90 60.8 140 78.2
41 34.0 91 61.3 141 78.4
42 34.6 92 61.7 142 78.7
43 35.3 93 62.1 143 79.0
44 36.0 94 62.5 144 79.2
45 36.6 95 62.9 145 79.5
46 37.3 96 63.3 146 79.8
47 37.9 97 63.8 147 80.0
48 38.6 98 64.2 148 80.3
49 39.2 99 64.6 149 80.5
50 39.9 100 65.0 150 80.8
"""


def parse_skill_percentages(raw_table: str) -> list[float]:
    table = [0.0] * 151
    for line in raw_table.strip().splitlines():
        parts = line.split()
        for index in range(0, len(parts), 2):
            table[int(parts[index])] = float(parts[index + 1])
    return table


SKILL_PERCENTAGES = parse_skill_percentages(SKILL_PERCENTAGE_TEXT)
DEFENCE_SKILL_SCALE = 0.867
AGILITY_SKILL_SCALE = 0.951
MAX_SCALED_SKILL_PERCENTAGE = SKILL_PERCENTAGES[-1]


@dataclass(frozen=True)
class SpellDefinition:
    name: str
    multiplier: float
    conversions: tuple[tuple[str, float], ...]
    note: str = ""


SPELLS_BY_WEAPON: dict[str, tuple[SpellDefinition, ...]] = {
    "wand": (
        SpellDefinition("Teleport", 1.0, (("t", 0.40),)),
        SpellDefinition("Meteor (Blast)", 5.0, (("e", 0.30), ("f", 0.30))),
        SpellDefinition("Meteor (Burn)", 1.0, ()),
        SpellDefinition("Ice Snake", 0.70, (("w", 0.50),)),
    ),
    "spear": (
        SpellDefinition("Bash (Both Hits)", 1.30, (("e", 0.40),), "Uses the PDF's total Bash multiplier with first-hit conversion."),
        SpellDefinition("Charge", 1.50, (("f", 0.40),)),
        SpellDefinition("Uppercut (First Hit)", 3.0, (("e", 0.20), ("t", 0.10))),
        SpellDefinition("Uppercut (Fireworks)", 0.50, (("t", 0.40),)),
        SpellDefinition("Uppercut (Crash)", 0.50, (("t", 0.20),)),
        SpellDefinition("War Scream (Area)", 0.50, (("f", 0.75), ("a", 0.25))),
        SpellDefinition("War Scream (Air Shout)", 0.30, (("f", 0.75), ("a", 0.25))),
    ),
    "bow": (
        SpellDefinition("Arrow Storm (Per Arrow)", 0.10, (("t", 0.25), ("f", 0.15))),
        SpellDefinition("Hawkeye (Per Arrow)", 0.80, ()),
        SpellDefinition("Escape", 1.0, (("a", 0.50),)),
        SpellDefinition("Bomb", 2.50, (("e", 0.25), ("f", 0.15))),
        SpellDefinition("Arrow Shield (Shield Hit)", 1.0, (("a", 0.30),)),
        SpellDefinition("Arrow Shield (Arrow Rain)", 2.0, (("a", 0.30),)),
    ),
    "dagger": (
        SpellDefinition("Spin Attack", 1.50, (("t", 0.30),)),
        SpellDefinition("Multihit (Hits 1-10)", 0.27, ()),
        SpellDefinition("Multihit (Fatality)", 1.20, (("e", 0.30), ("w", 0.50))),
        SpellDefinition("Smoke Bomb", 0.60, (("e", 0.25), ("a", 0.25))),
        SpellDefinition("Cherry Bomb", 1.10, ()),
    ),
    "relik": (
        SpellDefinition("Totem (Smash)", 1.0, (("f", 0.20),)),
        SpellDefinition("Totem (Tick)", 0.20, (("a", 0.20),)),
        SpellDefinition("Haul", 1.0, (("t", 0.20),)),
        SpellDefinition("Aura (Center)", 2.0, (("w", 0.30),)),
        SpellDefinition("Uproot", 1.0, (("e", 0.30),)),
    ),
}


@dataclass
class DamageRange:
    minimum: float = 0.0
    maximum: float = 0.0

    @classmethod
    def from_string(cls, raw_value: str | None) -> "DamageRange":
        if not raw_value:
            return cls()
        try:
            left, right = raw_value.split("-", 1)
            return cls(float(left), float(right))
        except ValueError:
            return cls()

    def clone(self) -> "DamageRange":
        return DamageRange(self.minimum, self.maximum)

    def add(self, other_min: float, other_max: float | None = None) -> None:
        self.minimum += other_min
        self.maximum += other_min if other_max is None else other_max

    def multiply(self, factor: float) -> None:
        self.minimum *= factor
        self.maximum *= factor

    def clamp_non_negative(self) -> None:
        self.minimum = max(0.0, self.minimum)
        self.maximum = max(0.0, self.maximum)


@dataclass
class DamageProfile:
    name: str
    attack_type: str
    noncrit: dict[str, DamageRange]
    crit: dict[str, DamageRange]
    crit_chance: float
    spell_multiplier: float
    attack_speed_multiplier: float
    attack_speed_label: str
    note: str = ""


@dataclass
class BuildResult:
    selected_items: dict[str, dict[str, Any]]
    base_skills: dict[str, int]
    base_skill_total: int
    allocation_metric_key: str | None
    allocation_metric_label: str
    allocation_objective: OptimizationObjective
    totals: dict[str, float]
    item_totals: dict[str, float]
    set_bonus_totals: dict[str, float]
    effective_skills: dict[str, int]
    active_sets: list[tuple[str, int, dict[str, float]]]
    equip_order: list[str] | None
    warnings: list[str]
    level_requirement: int
    gear_health_bonus: float
    weapon_class: str | None
    weapon: dict[str, Any] | None
    damage_profiles: dict[str, DamageProfile]


def is_number(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool))


def empty_damage_map() -> dict[str, DamageRange]:
    return {element: DamageRange() for element in ELEMENT_ORDER}


def deep_copy_damage_map(source: dict[str, DamageRange]) -> dict[str, DamageRange]:
    return {key: value.clone() for key, value in source.items()}


def format_number(value: float) -> str:
    if math.isclose(value, round(value), abs_tol=1e-9):
        return f"{int(round(value)):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def format_duration(seconds: float) -> str:
    safe_seconds = max(0.0, float(seconds))
    if safe_seconds < 1.0:
        return f"{safe_seconds:.2f}s"
    if safe_seconds < 60.0:
        return f"{safe_seconds:.1f}s"
    minutes, remainder = divmod(safe_seconds, 60.0)
    if safe_seconds < 3600.0:
        return f"{int(minutes)}m {int(round(remainder))}s"
    if safe_seconds < 86400.0:
        hours, minutes = divmod(minutes, 60.0)
        return f"{int(hours)}h {int(minutes)}m"
    days = safe_seconds / 86400.0
    if days < 14.0:
        return f"{days:.1f}d"
    if days < 365.0:
        return f"{int(round(days))}d"
    years = days / 365.25
    if years < 100.0:
        return f"{years:.1f}y"
    return f"{years:,.0f}y"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def format_damage_range(damage_range: DamageRange) -> str:
    return f"{format_number(damage_range.minimum)} - {format_number(damage_range.maximum)}"


def total_damage_range(damage_map: dict[str, DamageRange]) -> DamageRange:
    total = DamageRange()
    for damage_range in damage_map.values():
        total.add(damage_range.minimum, damage_range.maximum)
    return total


def combine_dicts(*parts: dict[str, float]) -> dict[str, float]:
    total: defaultdict[str, float] = defaultdict(float)
    for part in parts:
        for key, value in part.items():
            total[key] += value
    return dict(total)


def normalize_stat_key(key: str) -> str:
    if key in STAT_LABELS:
        return STAT_LABELS[key]
    return key


def default_mcts_worker_count(logical_cpus: int | None = None) -> int:
    detected = max(1, int(logical_cpus or DETECTED_LOGICAL_CPUS))
    return max(1, detected // 2)


def skill_tuple_to_dict(values: tuple[int, int, int, int, int]) -> dict[str, int]:
    return {
        skill: int(values[index])
        for index, skill in enumerate(SKILLS)
    }


def skill_dict_to_tuple(values: dict[str, int]) -> tuple[int, int, int, int, int]:
    return tuple(int(values.get(skill, 0)) for skill in SKILLS)


def level_105_allocation_feasible(values: tuple[int, int, int, int, int]) -> bool:
    return all(0 <= value <= LEVEL_105_MAX_BASE_SKILL for value in values) and sum(values) <= LEVEL_105_TOTAL_SKILL_POINTS


def level_105_allocation_shortfall(values: tuple[int, int, int, int, int]) -> int:
    over_cap = sum(max(0, value - LEVEL_105_MAX_BASE_SKILL) for value in values)
    over_total = max(0, sum(values) - LEVEL_105_TOTAL_SKILL_POINTS)
    return over_cap + over_total


def allocation_strategy_for_metric(metric_key: str) -> str:
    if metric_key == "melee_avg":
        return "melee"
    if metric_key == "spell_avg":
        return "spell"
    if metric_key == "effective_hp":
        return "effective_hp"
    if metric_key in MANA_ALLOCATION_METRICS:
        return "mana"
    return "minimal"


def expected_average_from_profile(profile: DamageProfile) -> float:
    noncrit = total_damage_range(profile.noncrit)
    crit = total_damage_range(profile.crit)
    expected = DamageRange(
        minimum=(noncrit.minimum * (1.0 - profile.crit_chance)) + (crit.minimum * profile.crit_chance),
        maximum=(noncrit.maximum * (1.0 - profile.crit_chance)) + (crit.maximum * profile.crit_chance),
    )
    return (expected.minimum + expected.maximum) / 2.0


def selection_signature(selections: dict[str, str]) -> tuple[str, ...]:
    return tuple(selections.get(slot_label, "") for slot_label, _slot_type in SLOT_CONFIGS)


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    kind: str
    relevant_keys: frozenset[str]


@dataclass(frozen=True)
class ObjectiveTerm:
    metric_key: str
    weight: float = 1.0


@dataclass(frozen=True)
class OptimizationObjective:
    terms: tuple[ObjectiveTerm, ...]
    normalized: bool = False
    scales: tuple[float, ...] = tuple()

    def is_single_metric(self) -> bool:
        return len(self.terms) == 1

    def primary_metric_key(self) -> str:
        if not self.terms:
            return "hp_total"
        return self.terms[0].metric_key

    def display_label(self) -> str:
        if self.is_single_metric():
            return METRIC_DEFINITIONS[self.primary_metric_key()].label
        return "Weighted Score"

    def short_description(self, max_terms: int = 3) -> str:
        if self.is_single_metric():
            return self.display_label()
        parts = [
            f"{METRIC_DEFINITIONS[term.metric_key].label} x{format_number(term.weight)}"
            for term in self.terms[:max_terms]
        ]
        if len(self.terms) > max_terms:
            parts.append("...")
        return ", ".join(parts)

    def full_description(self) -> str:
        if self.is_single_metric():
            return self.display_label()
        return ", ".join(
            f"{METRIC_DEFINITIONS[term.metric_key].label} x{format_number(term.weight)}"
            for term in self.terms
        )

    def normalized_weight(self, index: int) -> float:
        if self.is_single_metric():
            return 1.0
        total_weight = sum(max(0.0, term.weight) for term in self.terms)
        if total_weight <= 0.0:
            return 1.0 / max(1, len(self.terms))
        return max(0.0, self.terms[index].weight) / total_weight

    def scale_for_index(self, index: int, fallback: float = 1.0) -> float:
        if index < len(self.scales):
            return max(1.0, abs(float(self.scales[index])))
        return max(1.0, abs(float(fallback)))

    def with_scales(self, scales: list[float] | tuple[float, ...]) -> "OptimizationObjective":
        if self.is_single_metric():
            return self
        return OptimizationObjective(
            terms=self.terms,
            normalized=True,
            scales=tuple(max(1.0, abs(float(scale))) for scale in scales),
        )


@dataclass(frozen=True)
class OptimizationConstraint:
    metric_key: str
    operator: str
    target: float

    def display_label(self) -> str:
        return f"{METRIC_DEFINITIONS[self.metric_key].label} {self.operator} {format_number(self.target)}"


@dataclass
class BuildOption:
    score: float
    selections: dict[str, str]
    result: BuildResult
    objective_label: str
    objective_value: float
    objective: OptimizationObjective
    constraint_values: dict[str, float]


@dataclass(frozen=True)
class ExactSearchEstimate:
    estimated_seconds: float
    low_seconds: float
    high_seconds: float
    states_per_second: float
    sampled_states: int
    estimated_total_states: int
    raw_total_states: int
    completed_during_sample: bool
    candidate_group_sizes: tuple[int, ...]


@dataclass(frozen=True)
class CandidateFact:
    label: str
    slot_type: str
    item_type: str
    category: str
    totals: dict[str, float]
    skill_delta: tuple[int, int, int, int, int]
    req_tuple: tuple[int, int, int, int, int]
    set_name: str | None
    weapon_type: str | None
    melee_base: float
    spell_base: float
    level_requirement: int


@dataclass
class GroupCandidate:
    group_name: str
    selections: dict[str, str]
    item_labels: tuple[str, ...]
    totals: dict[str, float]
    set_counts: dict[str, int]
    req_minima: tuple[tuple[int, int, int, int, int], ...]
    weapon_label: str | None = None
    metric_vector: tuple[float, ...] = tuple()
    sort_vector: tuple[float, ...] = tuple()
    req_packed: tuple[tuple[int, int, int, int, int], ...] = tuple()


@dataclass
class SearchState:
    group_index: int
    selections: dict[str, str]
    item_labels: tuple[str, ...]
    item_totals: dict[str, float]
    set_counts: dict[str, int]
    weapon_label: str | None
    req_minima: tuple[tuple[int, int, int, int, int], ...]


@dataclass(frozen=True)
class SearchSolution:
    score: float
    objective_value: float
    selection_values: tuple[str, ...]
    base_skills: tuple[int, int, int, int, int]
    equip_order: tuple[str, ...]
    constraint_values: tuple[tuple[str, float], ...]

    def selections_dict(self) -> dict[str, str]:
        return {
            slot_label: self.selection_values[index]
            for index, (slot_label, _slot_type) in enumerate(SLOT_CONFIGS)
            if self.selection_values[index]
        }


@dataclass(frozen=True)
class PreparedSearchSpace:
    cache_id: tuple[Any, ...]
    metric_keys_for_candidates: frozenset[str]
    group_order: tuple[str, ...]
    group_candidates: tuple[tuple[GroupCandidate, ...], ...]
    remaining_stat_maxima: tuple[dict[str, float], ...]
    remaining_set_piece_caps: tuple[dict[str, int], ...]
    remaining_melee_base: tuple[float, ...]
    remaining_spell_base: tuple[float, ...]
    group_stat_maxima: tuple[dict[str, float], ...]
    group_set_caps: tuple[dict[str, int], ...]
    all_stat_maxima: dict[str, float]
    all_set_caps: dict[str, int]
    all_melee_base: float
    all_spell_base: float


@dataclass
class MCTSNode:
    state: SearchState
    parent: MCTSNode | None
    untried_indices: list[int]
    children: list[MCTSNode] = field(default_factory=list)
    visits: int = 0
    total_reward: float = 0.0
    best_reward: float = float("-inf")
    fully_explored: bool = False


def build_metric_definitions() -> dict[str, MetricDefinition]:
    definitions: dict[str, MetricDefinition] = {
        "hp_total": MetricDefinition("hp_total", "HP", "computed", frozenset({"hp", "hpBonus"})),
        "effective_hp": MetricDefinition("effective_hp", "Effective HP", "computed", frozenset({"hp", "hpBonus", "def", "agi"})),
        "melee_avg": MetricDefinition("melee_avg", "Melee Avg Damage", "computed", frozenset(MELEE_RELEVANT_KEYS)),
        "spell_avg": MetricDefinition("spell_avg", "Spell Avg Damage", "computed", frozenset(SPELL_RELEVANT_KEYS)),
    }
    for key, label in STAT_LABELS.items():
        definitions[key] = MetricDefinition(key, label, "stat", frozenset({key}))
    return definitions


METRIC_DEFINITIONS = build_metric_definitions()
METRIC_LABEL_TO_KEY = {definition.label.lower(): key for key, definition in METRIC_DEFINITIONS.items()}
for alias, metric_key in DIRECT_METRIC_ALIASES.items():
    METRIC_LABEL_TO_KEY[alias.lower()] = metric_key


def resolve_metric_key(raw_text: str) -> str | None:
    normalized = raw_text.strip().lower()
    if not normalized:
        return None
    if normalized in METRIC_LABEL_TO_KEY:
        return METRIC_LABEL_TO_KEY[normalized]
    for key, definition in METRIC_DEFINITIONS.items():
        if key.lower() == normalized:
            return key
    return None


METRIC_DISPLAY_OPTIONS = sorted(
    {definition.label for definition in METRIC_DEFINITIONS.values()},
    key=str.casefold,
)


def make_optimization_objective(
    entries: list[tuple[str, float]] | tuple[tuple[str, float], ...],
) -> OptimizationObjective:
    merged: dict[str, float] = {}
    ordered_keys: list[str] = []
    for metric_key, weight in entries:
        if metric_key not in METRIC_DEFINITIONS:
            continue
        numeric_weight = float(weight)
        if numeric_weight <= 0.0:
            continue
        if metric_key not in merged:
            ordered_keys.append(metric_key)
            merged[metric_key] = 0.0
        merged[metric_key] += numeric_weight

    if not ordered_keys:
        ordered_keys = ["hp_total"]
        merged = {"hp_total": 1.0}

    return OptimizationObjective(
        terms=tuple(
            ObjectiveTerm(metric_key=metric_key, weight=merged[metric_key])
            for metric_key in ordered_keys
        ),
    )


def coerce_optimization_objective(raw_objective: str | OptimizationObjective | None) -> OptimizationObjective:
    if isinstance(raw_objective, OptimizationObjective):
        if raw_objective.terms:
            return raw_objective
        return make_optimization_objective((("hp_total", 1.0),))
    if isinstance(raw_objective, str):
        metric_key = raw_objective if raw_objective in METRIC_DEFINITIONS else "hp_total"
        return make_optimization_objective(((metric_key, 1.0),))
    return make_optimization_objective((("hp_total", 1.0),))


class WynnBuildEngine:
    def __init__(self, data_path: Path) -> None:
        self.data_path = Path(data_path)
        with self.data_path.open("r", encoding="utf-8") as handle:
            raw_data = json.load(handle)

        self.items: list[dict[str, Any]] = raw_data["items"]
        self.sets: dict[str, dict[str, Any]] = raw_data.get("sets", {})
        self.item_lookup: dict[str, dict[str, Any]] = {}
        self.item_fact_lookup: dict[str, CandidateFact] = {}
        self.slot_options: dict[str, list[str]] = {slot: [] for slot, _ in SLOT_CONFIGS}
        self.slot_candidate_facts: dict[str, list[CandidateFact]] = {slot: [] for slot, _ in SLOT_CONFIGS}
        self._slot_option_level_cache: dict[tuple[str, int | None], list[str]] = {}
        self._slot_candidate_level_cache: dict[tuple[str, int | None], list[CandidateFact]] = {}
        self.item_to_set: dict[str, str] = {}
        self._set_skill_bonuses: dict[str, tuple[tuple[int, int, int, int, int], ...]] = {}
        self._requirement_minima_cache: dict[tuple[str, ...], tuple[tuple[int, int, int, int, int], ...]] = {}
        self.max_item_level = max((int(item.get("lvl", 0) or 0) for item in self.items), default=0)

        for set_name, set_data in self.sets.items():
            for item_name in set_data.get("items", []):
                self.item_to_set[item_name] = set_name
            bonuses = set_data.get("bonuses", [])
            piece_count = len(set_data.get("items", []))
            skill_bonus_rows: list[tuple[int, int, int, int, int]] = [(0, 0, 0, 0, 0)]
            for count in range(1, piece_count + 1):
                if bonuses:
                    bonus = bonuses[min(count - 1, len(bonuses) - 1)]
                else:
                    bonus = {}
                skill_bonus_rows.append(
                    tuple(int(float(bonus.get(skill, 0.0) or 0.0)) for skill in SKILLS)
                )
            self._set_skill_bonuses[set_name] = tuple(skill_bonus_rows)

        for item in self.items:
            label = item.get("displayName") or item.get("name")
            if not label:
                continue
            normalized_item = dict(item)
            normalized_item["_label"] = label
            self.item_lookup[label] = normalized_item
            self.item_fact_lookup[label] = self._build_candidate_fact(normalized_item)

        for slot_label, slot_type in SLOT_CONFIGS:
            if slot_type == "weapon":
                matching_facts = [
                    fact
                    for fact in self.item_fact_lookup.values()
                    if fact.category == "weapon"
                ]
            else:
                matching_facts = [
                    fact
                    for fact in self.item_fact_lookup.values()
                    if fact.item_type == slot_type
                ]
            matching = [fact.label for fact in matching_facts]
            self.slot_candidate_facts[slot_label] = sorted(matching_facts, key=lambda fact: fact.label.casefold())
            self.slot_options[slot_label] = sorted(matching, key=str.casefold)

    def slot_candidate_facts_for_level(self, slot_label: str, max_level: int | None = None) -> list[CandidateFact]:
        cache_key = (slot_label, None if max_level is None else int(max_level))
        cached = self._slot_candidate_level_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        source = self.slot_candidate_facts[slot_label]
        if max_level is None:
            filtered = list(source)
        else:
            safe_level = int(max_level)
            filtered = [fact for fact in source if fact.level_requirement <= safe_level]
        self._slot_candidate_level_cache[cache_key] = filtered
        return list(filtered)

    def slot_options_for_level(self, slot_label: str, max_level: int | None = None) -> list[str]:
        cache_key = (slot_label, None if max_level is None else int(max_level))
        cached = self._slot_option_level_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        labels = [fact.label for fact in self.slot_candidate_facts_for_level(slot_label, max_level)]
        self._slot_option_level_cache[cache_key] = labels
        return list(labels)

    def _build_candidate_fact(self, item: dict[str, Any]) -> CandidateFact:
        totals = {
            key: float(value)
            for key, value in item.items()
            if is_number(value)
        }
        weapon_type = str(item.get("type", "")) if item.get("category") == "weapon" else None
        return CandidateFact(
            label=item["_label"],
            slot_type=str(item.get("type", "")),
            item_type=str(item.get("type", "")),
            category=str(item.get("category", "")),
            totals=totals,
            skill_delta=tuple(int(float(item.get(skill, 0.0) or 0.0)) for skill in SKILLS),
            req_tuple=tuple(int(item.get(req_key, 0) or 0) for req_key in REQ_KEYS),
            set_name=self.item_to_set.get(item["_label"]),
            weapon_type=weapon_type,
            melee_base=self.weapon_melee_base_average(item) if item.get("category") == "weapon" else 0.0,
            spell_base=float(item.get("averageDps", 0.0) or 0.0) if item.get("category") == "weapon" else 0.0,
            level_requirement=int(item.get("lvl", 0) or 0),
        )

    def item_facts_for_labels(self, labels: tuple[str, ...]) -> tuple[CandidateFact, ...]:
        return tuple(self.item_fact_lookup[label] for label in labels)

    def set_skill_bonus_tuple(self, set_name: str, piece_count: int) -> tuple[int, int, int, int, int]:
        if piece_count <= 0:
            return (0, 0, 0, 0, 0)
        bonus_rows = self._set_skill_bonuses.get(set_name)
        if not bonus_rows:
            return (0, 0, 0, 0, 0)
        safe_count = min(piece_count, len(bonus_rows) - 1)
        return bonus_rows[safe_count]

    def set_skill_bonus_delta(self, set_name: str, before_count: int, after_count: int) -> tuple[int, int, int, int, int]:
        before = self.set_skill_bonus_tuple(set_name, before_count)
        after = self.set_skill_bonus_tuple(set_name, after_count)
        return tuple(after[index] - before[index] for index in range(5))

    def build_result(
        self,
        selections: dict[str, str],
        preferred_metric: str | OptimizationObjective = "hp_total",
        constraints: tuple[OptimizationConstraint, ...] | None = None,
    ) -> BuildResult:
        warnings: list[str] = []
        selected_items: dict[str, dict[str, Any]] = {}

        for slot_label, _slot_type in SLOT_CONFIGS:
            raw_label = selections.get(slot_label, "").strip()
            if not raw_label:
                continue
            item = self.item_lookup.get(raw_label)
            if item is None:
                warnings.append(f"{slot_label}: '{raw_label}' was not recognized.")
                continue
            selected_items[slot_label] = item

        item_totals = self._sum_numeric_stats(selected_items.values())
        set_bonus_totals, active_sets = self._compute_active_sets(list(selected_items.values()))
        totals = combine_dicts(item_totals, set_bonus_totals)
        level_requirement = max((int(item.get("lvl", 0)) for item in selected_items.values()), default=0)
        gear_health_bonus = totals.get("hp", 0.0) + totals.get("hpBonus", 0.0)

        equip_order: list[str] | None = []
        chosen_base_skills = {skill: 0 for skill in SKILLS}
        chosen_objective = coerce_optimization_objective(preferred_metric)
        chosen_metric = chosen_objective.primary_metric_key() if chosen_objective.is_single_metric() else None

        if selected_items:
            optimized_base_skills = self._optimize_level_105_base_skills(
                selected_items,
                totals,
                chosen_objective,
                tuple(constraints or ()),
            )
            if optimized_base_skills is None:
                equip_order = None
                warnings.append(
                    f"This selection cannot be legally and stably equipped by a level 105 build with {LEVEL_105_TOTAL_SKILL_POINTS} total base points and {LEVEL_105_MAX_BASE_SKILL} max in any stat."
                )
            else:
                chosen_base_skills = optimized_base_skills
                equip_order = self._find_equip_order(selected_items, chosen_base_skills)
                if equip_order is None:
                    warnings.append(
                        "This selection cannot stay legally equipped with a stable order under the level 105 skill-point budget."
                    )
        else:
            chosen_base_skills = {skill: 0 for skill in SKILLS}

        effective_skills = {
            skill: int(chosen_base_skills.get(skill, 0) + totals.get(skill, 0))
            for skill in SKILLS
        }

        weapon = selected_items.get("Weapon")
        weapon_class = None
        damage_profiles: dict[str, DamageProfile] = {}
        if weapon:
            weapon_class = weapon.get("classReq") or WEAPON_CLASS_NAMES.get(str(weapon.get("type")))
            damage_profiles = self._compute_damage_profiles(weapon, totals, effective_skills)

        return BuildResult(
            selected_items=selected_items,
            base_skills=chosen_base_skills,
            base_skill_total=sum(chosen_base_skills.values()),
            allocation_metric_key=chosen_metric,
            allocation_metric_label=chosen_objective.full_description(),
            allocation_objective=chosen_objective,
            totals=totals,
            item_totals=item_totals,
            set_bonus_totals=set_bonus_totals,
            effective_skills=effective_skills,
            active_sets=active_sets,
            equip_order=equip_order,
            warnings=warnings,
            level_requirement=level_requirement,
            gear_health_bonus=gear_health_bonus,
            weapon_class=weapon_class,
            weapon=weapon,
            damage_profiles=damage_profiles,
        )

    def _sum_numeric_stats(self, items: list[dict[str, Any]] | Any) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)
        for item in items:
            for key, value in item.items():
                if is_number(value):
                    totals[key] += value
        return dict(totals)

    def _compute_active_sets(self, items: list[dict[str, Any]]) -> tuple[dict[str, float], list[tuple[str, int, dict[str, float]]]]:
        counts: Counter[str] = Counter()
        for item in items:
            label = item["_label"]
            set_name = self.item_to_set.get(label)
            if set_name:
                counts[set_name] += 1

        total_bonus: defaultdict[str, float] = defaultdict(float)
        active: list[tuple[str, int, dict[str, float]]] = []

        for set_name, piece_count in sorted(counts.items()):
            bonuses = self.sets.get(set_name, {}).get("bonuses", [])
            if not bonuses:
                continue
            bonus_index = min(piece_count - 1, len(bonuses) - 1)
            bonus = dict(bonuses[bonus_index])
            for key, value in bonus.items():
                if is_number(value):
                    total_bonus[key] += float(value)
            if piece_count > 1 or bonus:
                active.append((set_name, piece_count, bonus))

        return dict(total_bonus), active

    def _optimize_level_105_base_skills(
        self,
        selected_items: dict[str, dict[str, Any]],
        totals: dict[str, float],
        preferred_metric: str | OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
    ) -> dict[str, int] | None:
        objective = coerce_optimization_objective(preferred_metric)
        item_labels = tuple(
            selected_items[slot]["_label"]
            for slot, _slot_type in SLOT_CONFIGS
            if slot in selected_items
        )
        minima_options = self.requirement_minima_for_labels(item_labels)
        return self._optimize_level_105_base_skills_from_minima(
            minima_options,
            totals,
            selected_items.get("Weapon"),
            objective,
            constraints,
        )

    def _optimize_level_105_base_skills_from_minima(
        self,
        minima_options: tuple[tuple[int, int, int, int, int], ...],
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        preferred_metric: str | OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
    ) -> dict[str, int] | None:
        objective = coerce_optimization_objective(preferred_metric)
        feasible = [option for option in minima_options if level_105_allocation_feasible(option)]
        if not feasible:
            return None

        best_allocation: tuple[int, int, int, int, int] | None = None
        best_utility: tuple[float, ...] | None = None

        for minima in feasible:
            expanded = self._greedy_expand_allocation(minima, totals, weapon, objective, constraints)
            refined = self._refine_allocation(minima, expanded, totals, weapon, objective, constraints)
            utility = self._allocation_utility(refined, totals, weapon, objective, constraints)
            if best_utility is None or utility > best_utility:
                best_allocation = refined
                best_utility = utility

        return skill_tuple_to_dict(best_allocation) if best_allocation is not None else None

    def _greedy_expand_allocation(
        self,
        minima: tuple[int, int, int, int, int],
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        preferred_metric: str | OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
    ) -> tuple[int, int, int, int, int]:
        current = list(minima)
        current_utility = self._allocation_utility(tuple(current), totals, weapon, preferred_metric, constraints)

        while sum(current) < LEVEL_105_TOTAL_SKILL_POINTS:
            best_index: int | None = None
            best_utility: tuple[float, ...] | None = None
            for skill_index in range(5):
                if current[skill_index] >= LEVEL_105_MAX_BASE_SKILL:
                    continue
                current[skill_index] += 1
                utility = self._allocation_utility(tuple(current), totals, weapon, preferred_metric, constraints)
                current[skill_index] -= 1
                if best_utility is None or utility > best_utility:
                    best_index = skill_index
                    best_utility = utility

            if best_index is None or best_utility is None or best_utility <= current_utility:
                break

            current[best_index] += 1
            current_utility = best_utility

        return tuple(current)

    def _refine_allocation(
        self,
        minima: tuple[int, int, int, int, int],
        allocation: tuple[int, int, int, int, int],
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        preferred_metric: str | OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
    ) -> tuple[int, int, int, int, int]:
        current = list(allocation)
        current_utility = self._allocation_utility(tuple(current), totals, weapon, preferred_metric, constraints)

        improved = True
        while improved:
            improved = False
            for take_index in range(5):
                if current[take_index] <= minima[take_index]:
                    continue
                for give_index in range(5):
                    if give_index == take_index or current[give_index] >= LEVEL_105_MAX_BASE_SKILL:
                        continue
                    current[take_index] -= 1
                    current[give_index] += 1
                    utility = self._allocation_utility(tuple(current), totals, weapon, preferred_metric, constraints)
                    if utility > current_utility:
                        current_utility = utility
                        improved = True
                        break
                    current[take_index] += 1
                    current[give_index] -= 1
                if improved:
                    break

        return tuple(current)

    def _allocation_utility(
        self,
        allocation: tuple[int, int, int, int, int],
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        preferred_metric: str | OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
    ) -> tuple[float, ...]:
        objective = coerce_optimization_objective(preferred_metric)
        satisfied = 1.0
        penalty = 0.0
        for constraint in constraints:
            value = self._metric_value_from_parts(constraint.metric_key, totals, weapon, allocation)
            if not BuildOptimizer._constraint_matches(value, constraint):
                satisfied = 0.0
                penalty += BuildOptimizer._constraint_penalty(value, constraint)

        primary_score = self._allocation_objective_value(objective, totals, weapon, allocation)
        return (
            satisfied,
            -penalty,
            primary_score,
            -float(sum(allocation)),
            *[-float(value) for value in allocation],
        )

    def _allocation_support_value(
        self,
        preferred_metric: str,
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        allocation: tuple[int, int, int, int, int],
    ) -> float:
        strategy = allocation_strategy_for_metric(preferred_metric)
        if strategy == "mana":
            effective_int = allocation[2] + int(totals.get("int", 0.0))
            return float(effective_int) + (self._skill_effect_percentage("int", effective_int) / 100.0)
        if strategy == "minimal":
            return 0.0
        return self._metric_value_from_parts(preferred_metric, totals, weapon, allocation)

    def _allocation_objective_value(
        self,
        objective: OptimizationObjective,
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        allocation: tuple[int, int, int, int, int],
    ) -> float:
        if objective.is_single_metric():
            return self._allocation_support_value(objective.primary_metric_key(), totals, weapon, allocation)

        total = 0.0
        for index, term in enumerate(objective.terms):
            support_value = self._allocation_support_value(term.metric_key, totals, weapon, allocation)
            reference_scale = self._allocation_reference_scale(term.metric_key, totals, weapon, allocation)
            scale = objective.scale_for_index(index, reference_scale)
            total += objective.normalized_weight(index) * (support_value / scale)
        return total

    def _allocation_reference_scale(
        self,
        metric_key: str,
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        allocation: tuple[int, int, int, int, int],
    ) -> float:
        if metric_key in MANA_ALLOCATION_METRICS:
            optimistic = list(allocation)
            optimistic[2] = LEVEL_105_MAX_BASE_SKILL
            return self._allocation_support_value(metric_key, totals, weapon, tuple(optimistic))

        optimistic = []
        remaining = LEVEL_105_TOTAL_SKILL_POINTS
        for index, base_value in enumerate(allocation):
            optimistic_value = max(int(base_value), 0)
            optimistic_value = min(LEVEL_105_MAX_BASE_SKILL, optimistic_value)
            optimistic.append(optimistic_value)
            remaining -= optimistic_value
        skill_priority = {
            "melee_avg": ("str", "dex"),
            "spell_avg": ("str", "dex", "int"),
            "effective_hp": ("def", "agi"),
        }.get(metric_key, ())
        for skill_name in skill_priority:
            skill_index = SKILLS.index(skill_name)
            take = min(remaining, LEVEL_105_MAX_BASE_SKILL - optimistic[skill_index])
            optimistic[skill_index] += take
            remaining -= take
            if remaining <= 0:
                break
        if remaining > 0:
            for skill_index in range(5):
                take = min(remaining, LEVEL_105_MAX_BASE_SKILL - optimistic[skill_index])
                optimistic[skill_index] += take
                remaining -= take
                if remaining <= 0:
                    break
        return max(1.0, self._metric_value_from_parts(metric_key, totals, weapon, tuple(optimistic)))

    def _metric_value_from_parts(
        self,
        metric_key: str,
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        allocation: tuple[int, int, int, int, int],
    ) -> float:
        if metric_key == "hp_total":
            return float(totals.get("hp", 0.0) + totals.get("hpBonus", 0.0))

        effective_skills = {
            skill: int(allocation[index] + totals.get(skill, 0.0))
            for index, skill in enumerate(SKILLS)
        }

        if metric_key == "effective_hp":
            return self._effective_hp_value(totals, effective_skills)
        if metric_key in {"melee_avg", "spell_avg"} and weapon is not None:
            profiles = self._compute_damage_profiles(weapon, totals, effective_skills)
            profile = profiles.get("Melee" if metric_key == "melee_avg" else "Spell")
            return expected_average_from_profile(profile) if profile else 0.0
        return float(totals.get(metric_key, 0.0))

    def _requirement_minima_for_items(
        self,
        items: tuple[dict[str, Any], ...],
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        labels = tuple(item["_label"] for item in items)
        return self.requirement_minima_for_labels(labels)

    def requirement_minima_for_labels(
        self,
        item_labels: tuple[str, ...],
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        normalized = tuple(sorted(item_labels))
        cached = self._requirement_minima_cache.get(normalized)
        if cached is not None:
            return cached
        facts = self.item_facts_for_labels(normalized)
        minima = self._requirement_minima_for_facts(facts)
        self._requirement_minima_cache[normalized] = minima
        return minima

    def _requirement_minima_for_facts(
        self,
        facts: tuple[CandidateFact, ...],
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        item_count = len(facts)
        if item_count == 0:
            return ((0, 0, 0, 0, 0),)

        mask_count = 1 << item_count
        zero_skills = (0, 0, 0, 0, 0)
        skill_bonus_by_mask: list[tuple[int, int, int, int, int]] = [zero_skills for _ in range(mask_count)]
        max_req_by_mask: list[tuple[int, int, int, int, int]] = [zero_skills for _ in range(mask_count)]
        stable_need_by_mask: list[tuple[int, int, int, int, int]] = [zero_skills for _ in range(mask_count)]
        set_counts_by_mask: list[dict[str, int]] = [{} for _ in range(mask_count)]

        for mask in range(1, mask_count):
            lowest_bit = mask & -mask
            item_index = lowest_bit.bit_length() - 1
            prev_mask = mask ^ lowest_bit
            fact = facts[item_index]

            prev_bonus = skill_bonus_by_mask[prev_mask]
            new_bonus = [prev_bonus[index] + fact.skill_delta[index] for index in range(5)]

            prev_set_counts = set_counts_by_mask[prev_mask]
            next_set_counts = dict(prev_set_counts)
            if fact.set_name:
                before_count = prev_set_counts.get(fact.set_name, 0)
                after_count = before_count + 1
                next_set_counts[fact.set_name] = after_count
                skill_delta = self.set_skill_bonus_delta(fact.set_name, before_count, after_count)
                for index in range(5):
                    new_bonus[index] += skill_delta[index]
            set_counts_by_mask[mask] = next_set_counts
            skill_bonus_by_mask[mask] = tuple(new_bonus)

            prev_max_req = max_req_by_mask[prev_mask]
            current_max_req = tuple(max(prev_max_req[index], fact.req_tuple[index]) for index in range(5))
            max_req_by_mask[mask] = current_max_req
            stable_need_by_mask[mask] = tuple(
                max(0, current_max_req[index] - skill_bonus_by_mask[mask][index])
                for index in range(5)
            )

        pareto: dict[int, list[tuple[int, int, int, int, int]]] = {0: [zero_skills]}
        for mask in range(1, mask_count):
            stable_need = stable_need_by_mask[mask]
            candidates: list[tuple[int, int, int, int, int]] = []
            for item_index in range(item_count):
                bit = 1 << item_index
                if not (mask & bit):
                    continue
                prev_mask = mask ^ bit
                prev_bonus = skill_bonus_by_mask[prev_mask]
                req_tuple = facts[item_index].req_tuple
                for base_need in pareto[prev_mask]:
                    candidate = tuple(
                        max(
                            stable_need[skill_index],
                            base_need[skill_index],
                            max(0, req_tuple[skill_index] - prev_bonus[skill_index]),
                        )
                        for skill_index in range(5)
                    )
                    candidates.append(candidate)
            pareto[mask] = self._pareto_reduce_skill_requirements(candidates)

        return tuple(sorted(pareto[mask_count - 1]))

    @staticmethod
    def _pareto_reduce_skill_requirements(
        candidates: list[tuple[int, int, int, int, int]],
    ) -> list[tuple[int, int, int, int, int]]:
        if not candidates:
            return [(0, 0, 0, 0, 0)]

        minima: list[tuple[int, int, int, int, int]] = []
        for candidate in sorted(candidates, key=lambda values: (sum(values), values)):
            dominated = False
            kept: list[tuple[int, int, int, int, int]] = []
            for existing in minima:
                if all(existing[index] <= candidate[index] for index in range(5)):
                    dominated = True
                    break
                if all(candidate[index] <= existing[index] for index in range(5)):
                    continue
                kept.append(existing)
            if not dominated:
                kept.append(candidate)
                minima = kept
        return minima

    def _find_equip_order(self, selected_items: dict[str, dict[str, Any]], base_skills: dict[str, int]) -> list[str] | None:
        if not selected_items:
            return []

        slot_names = tuple(slot for slot, _ in SLOT_CONFIGS if slot in selected_items)

        @lru_cache(maxsize=None)
        def current_skill_totals(equipped_slots: tuple[str, ...]) -> dict[str, int]:
            equipped_items = [selected_items[slot] for slot in equipped_slots]
            item_totals = self._sum_numeric_stats(equipped_items)
            set_totals, _active_sets = self._compute_active_sets(equipped_items)
            return {
                skill: int(base_skills.get(skill, 0) + item_totals.get(skill, 0) + set_totals.get(skill, 0))
                for skill in SKILLS
            }

        def equipped_subset_is_stable(equipped_slots: tuple[str, ...], skill_totals: dict[str, int]) -> bool:
            return all(
                self._requirements_met(selected_items[slot], skill_totals)
                for slot in equipped_slots
            )

        @lru_cache(maxsize=None)
        def search(remaining_slots: tuple[str, ...]) -> tuple[str, ...] | None:
            if not remaining_slots:
                return tuple()

            equipped_slots = tuple(slot for slot in slot_names if slot not in remaining_slots)
            skills_now = current_skill_totals(equipped_slots)

            for slot in remaining_slots:
                item = selected_items[slot]
                if self._requirements_met(item, skills_now):
                    next_equipped = equipped_slots + (slot,)
                    next_skills = current_skill_totals(next_equipped)
                    if not equipped_subset_is_stable(next_equipped, next_skills):
                        continue
                    next_remaining = tuple(other for other in remaining_slots if other != slot)
                    suffix = search(next_remaining)
                    if suffix is not None:
                        return (slot,) + suffix
            return None

        result = search(slot_names)
        return list(result) if result is not None else None

    @staticmethod
    def _requirements_met(item: dict[str, Any], skill_totals: dict[str, int]) -> bool:
        for req_key, skill_key in REQ_KEYS.items():
            if int(item.get(req_key, 0)) > skill_totals.get(skill_key, 0):
                return False
        return True

    def _compute_damage_profiles(
        self,
        weapon: dict[str, Any],
        totals: dict[str, float],
        effective_skills: dict[str, int],
    ) -> dict[str, DamageProfile]:
        base_damage = {
            element: DamageRange.from_string(weapon.get(f"{element}Dam"))
            for element in ELEMENT_ORDER
        }
        crit_chance = self._skill_effect_percentage("dex", effective_skills["dex"]) / 100.0
        profiles: dict[str, DamageProfile] = {}

        melee_noncrit = self._finish_damage_pipeline(
            damage_map=deep_copy_damage_map(base_damage),
            totals=totals,
            effective_skills=effective_skills,
            attack_type="melee",
            crit=False,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
        )
        melee_crit = self._finish_damage_pipeline(
            damage_map=deep_copy_damage_map(base_damage),
            totals=totals,
            effective_skills=effective_skills,
            attack_type="melee",
            crit=True,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
        )
        profiles["Melee"] = DamageProfile(
            name="Melee",
            attack_type="melee",
            noncrit=melee_noncrit,
            crit=melee_crit,
            crit_chance=crit_chance,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
            attack_speed_label=str(weapon.get("atkSpd", "UNKNOWN")).replace("_", " ").title(),
        )

        generic_spell_base = self._build_generic_spell_damage_map(weapon, base_damage)
        spell_noncrit = self._finish_damage_pipeline(
            damage_map=generic_spell_base,
            totals=totals,
            effective_skills=effective_skills,
            attack_type="spell",
            crit=False,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
        )
        spell_crit = self._finish_damage_pipeline(
            damage_map=self._build_generic_spell_damage_map(weapon, base_damage),
            totals=totals,
            effective_skills=effective_skills,
            attack_type="spell",
            crit=True,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
        )
        profiles["Spell"] = DamageProfile(
            name="Spell",
            attack_type="spell",
            noncrit=spell_noncrit,
            crit=spell_crit,
            crit_chance=crit_chance,
            spell_multiplier=1.0,
            attack_speed_multiplier=1.0,
            attack_speed_label="Base DPS",
            note="Generic spell estimate scaled from the weapon's listed DPS.",
        )

        return profiles

    @staticmethod
    def _build_generic_spell_damage_map(
        weapon: dict[str, Any],
        base_damage: dict[str, DamageRange],
    ) -> dict[str, DamageRange]:
        average_dps = float(weapon.get("averageDps", 0.0) or 0.0)
        if average_dps <= 0:
            return empty_damage_map()

        midpoint_total = sum((damage.minimum + damage.maximum) / 2.0 for damage in base_damage.values())
        if midpoint_total <= 0:
            fallback = empty_damage_map()
            fallback["n"] = DamageRange(average_dps, average_dps)
            return fallback

        scale = average_dps / midpoint_total
        scaled = deep_copy_damage_map(base_damage)
        for damage_range in scaled.values():
            damage_range.multiply(scale)
        return scaled

    def _finish_damage_pipeline(
        self,
        damage_map: dict[str, DamageRange],
        totals: dict[str, float],
        effective_skills: dict[str, int],
        attack_type: str,
        crit: bool,
        spell_multiplier: float,
        attack_speed_multiplier: float,
    ) -> dict[str, DamageRange]:
        result = deep_copy_damage_map(damage_map)

        for element in ELEMENT_ORDER:
            boost_percent = self._damage_boost_percent(element, attack_type, totals, effective_skills, crit)
            result[element].multiply(max(0.0, 1.0 + (boost_percent / 100.0)))
            result[element].clamp_non_negative()

        if attack_type == "spell":
            for damage_range in result.values():
                damage_range.multiply(attack_speed_multiplier)

        for element in ELEMENT_ORDER:
            raw_bonus = self._raw_damage_bonus(element, attack_type, totals)
            result[element].add(raw_bonus)
            result[element].clamp_non_negative()

        if attack_type == "spell":
            for damage_range in result.values():
                damage_range.multiply(spell_multiplier)

        return result

    def _damage_boost_percent(
        self,
        element: str,
        attack_type: str,
        totals: dict[str, float],
        effective_skills: dict[str, int],
        crit: bool,
    ) -> float:
        generic_percent_key = "mdPct" if attack_type == "melee" else "sdPct"
        rainbow_percent_key = "rMdPct" if attack_type == "melee" else "rSdPct"
        element_percent_suffix = "MdPct" if attack_type == "melee" else "SdPct"
        critical_bonus = 100.0 + totals.get("critDamPct", 0.0) if crit else 0.0

        boost = totals.get("damPct", 0.0) + totals.get(generic_percent_key, 0.0)
        boost += self._skill_effect_percentage("str", effective_skills["str"])

        if element == "n":
            boost += totals.get("nDamPct", 0.0)
            boost += totals.get(f"n{element_percent_suffix}", 0.0)
        else:
            element_skill = ELEMENT_TO_SKILL[element]
            elemental_skill_bonus = self._skill_effect_percentage(element_skill, effective_skills[element_skill])
            boost += totals.get("rDamPct", 0.0)
            boost += totals.get(rainbow_percent_key, 0.0)
            boost += totals.get(f"{element}DamPct", 0.0)
            boost += totals.get(f"{element}{element_percent_suffix}", 0.0)
            boost += elemental_skill_bonus
            if crit and element == "t" and elemental_skill_bonus > 0.0:
                boost += (elemental_skill_bonus * critical_bonus) / 100.0

        if crit:
            boost += critical_bonus

        return boost

    @staticmethod
    def _raw_damage_bonus(element: str, attack_type: str, totals: dict[str, float]) -> float:
        generic_attack_raw_key = "mdRaw" if attack_type == "melee" else "sdRaw"
        rainbow_attack_raw_key = "rMdRaw" if attack_type == "melee" else "rSdRaw"
        element_raw_suffix = "MdRaw" if attack_type == "melee" else "SdRaw"

        if element == "n":
            return (
                totals.get("damRaw", 0.0)
                + totals.get(generic_attack_raw_key, 0.0)
                + totals.get("nDamRaw", 0.0)
                + totals.get(f"n{element_raw_suffix}", 0.0)
            )

        return (
            totals.get(f"{element}DamRaw", 0.0)
            + totals.get(f"{element}{element_raw_suffix}", 0.0)
            + totals.get("rDamRaw", 0.0)
            + totals.get(rainbow_attack_raw_key, 0.0)
        )

    @staticmethod
    def _skill_percentage(points: int) -> float:
        safe_points = max(0, min(150, int(points)))
        return SKILL_PERCENTAGES[safe_points]

    @classmethod
    def _skill_effect_percentage(cls, skill: str, points: int) -> float:
        base_percentage = cls._skill_percentage(points)
        if skill == "def":
            return base_percentage * DEFENCE_SKILL_SCALE
        if skill == "agi":
            return base_percentage * AGILITY_SKILL_SCALE
        return base_percentage

    @classmethod
    def _intelligence_spell_cost_reduction_percentage(cls, points: int) -> float:
        scaled_intelligence = cls._skill_effect_percentage("int", points)
        if scaled_intelligence <= 0.0:
            return 0.0
        return 50.0 * (scaled_intelligence / MAX_SCALED_SKILL_PERCENTAGE)

    def _effective_hp_value(self, totals: dict[str, float], effective_skills: dict[str, int]) -> float:
        base_hp = float(totals.get("hp", 0.0) + totals.get("hpBonus", 0.0))
        if base_hp <= 0:
            return 0.0

        defense_reduction = self._skill_effect_percentage("def", effective_skills["def"]) / 100.0
        dodge_chance = self._skill_effect_percentage("agi", effective_skills["agi"]) / 100.0
        expected_damage_multiplier = (dodge_chance * 0.1) + ((1.0 - dodge_chance) * (1.0 - defense_reduction))
        return base_hp / max(1e-9, expected_damage_multiplier)

    def set_bonus_for_count(self, set_name: str, piece_count: int) -> dict[str, float]:
        if piece_count <= 0:
            return {}
        bonuses = self.sets.get(set_name, {}).get("bonuses", [])
        if not bonuses:
            return {}
        bonus_index = min(piece_count - 1, len(bonuses) - 1)
        bonus = bonuses[bonus_index]
        return {
            key: float(value)
            for key, value in bonus.items()
            if is_number(value)
        }

    def set_bonus_totals_from_counts(self, set_counts: dict[str, int]) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)
        for set_name, count in set_counts.items():
            for key, value in self.set_bonus_for_count(set_name, count).items():
                totals[key] += value
        return dict(totals)

    @staticmethod
    def weapon_melee_base_average(weapon: dict[str, Any]) -> float:
        total = 0.0
        for element in ELEMENT_ORDER:
            damage = DamageRange.from_string(weapon.get(f"{element}Dam"))
            total += (damage.minimum + damage.maximum) / 2.0
        return total

    def metric_value_from_result(self, result: BuildResult, metric_key: str) -> float:
        if metric_key == "hp_total":
            return float(result.gear_health_bonus)
        if metric_key == "effective_hp":
            return self._effective_hp_value(result.totals, result.effective_skills)
        if metric_key == "melee_avg":
            profile = result.damage_profiles.get("Melee")
            return expected_average_from_profile(profile) if profile else 0.0
        if metric_key == "spell_avg":
            profile = result.damage_profiles.get("Spell")
            return expected_average_from_profile(profile) if profile else 0.0
        return float(result.totals.get(metric_key, 0.0))

    def objective_value_from_parts(
        self,
        totals: dict[str, float],
        weapon: dict[str, Any] | None,
        allocation: tuple[int, int, int, int, int],
        objective: str | OptimizationObjective,
    ) -> float:
        objective_spec = coerce_optimization_objective(objective)
        if objective_spec.is_single_metric():
            return self._metric_value_from_parts(objective_spec.primary_metric_key(), totals, weapon, allocation)

        total = 0.0
        for index, term in enumerate(objective_spec.terms):
            raw_value = self._metric_value_from_parts(term.metric_key, totals, weapon, allocation)
            scale = objective_spec.scale_for_index(index, raw_value)
            total += objective_spec.normalized_weight(index) * (raw_value / scale)
        return total

    def build_result_from_solution(
        self,
        solution: SearchSolution,
        objective: str | OptimizationObjective,
    ) -> BuildResult:
        objective_spec = coerce_optimization_objective(objective)
        selections = solution.selections_dict()
        selected_items = {
            slot_label: self.item_lookup[label]
            for slot_label, label in selections.items()
            if label in self.item_lookup
        }
        item_totals = self._sum_numeric_stats(selected_items.values())
        set_bonus_totals, active_sets = self._compute_active_sets(list(selected_items.values()))
        totals = combine_dicts(item_totals, set_bonus_totals)
        base_skills = skill_tuple_to_dict(solution.base_skills)
        effective_skills = {
            skill: int(base_skills.get(skill, 0) + totals.get(skill, 0))
            for skill in SKILLS
        }
        weapon = selected_items.get("Weapon")
        weapon_class = None
        damage_profiles: dict[str, DamageProfile] = {}
        if weapon:
            weapon_class = weapon.get("classReq") or WEAPON_CLASS_NAMES.get(str(weapon.get("type")))
            damage_profiles = self._compute_damage_profiles(weapon, totals, effective_skills)

        return BuildResult(
            selected_items=selected_items,
            base_skills=base_skills,
            base_skill_total=sum(base_skills.values()),
            allocation_metric_key=objective_spec.primary_metric_key() if objective_spec.is_single_metric() else None,
            allocation_metric_label=objective_spec.full_description(),
            allocation_objective=objective_spec,
            totals=totals,
            item_totals=item_totals,
            set_bonus_totals=set_bonus_totals,
            effective_skills=effective_skills,
            active_sets=active_sets,
            equip_order=list(solution.equip_order),
            warnings=[],
            level_requirement=max((int(item.get("lvl", 0)) for item in selected_items.values()), default=0),
            gear_health_bonus=totals.get("hp", 0.0) + totals.get("hpBonus", 0.0),
            weapon_class=weapon_class,
            weapon=weapon,
            damage_profiles=damage_profiles,
        )

    def objective_value_from_result(
        self,
        result: BuildResult,
        objective: str | OptimizationObjective,
    ) -> float:
        objective_spec = coerce_optimization_objective(objective)
        if objective_spec.is_single_metric():
            return self.metric_value_from_result(result, objective_spec.primary_metric_key())

        total = 0.0
        for index, term in enumerate(objective_spec.terms):
            raw_value = self.metric_value_from_result(result, term.metric_key)
            fallback_scale = self._result_reference_scale(result, term.metric_key)
            scale = objective_spec.scale_for_index(index, fallback_scale)
            total += objective_spec.normalized_weight(index) * (raw_value / scale)
        return total

    def objective_breakdown_from_result(
        self,
        result: BuildResult,
        objective: str | OptimizationObjective,
    ) -> list[tuple[str, float, float, float]]:
        objective_spec = coerce_optimization_objective(objective)
        breakdown: list[tuple[str, float, float, float]] = []
        for index, term in enumerate(objective_spec.terms):
            raw_value = self.metric_value_from_result(result, term.metric_key)
            if objective_spec.is_single_metric():
                contribution = raw_value
                scale = raw_value if not math.isclose(raw_value, 0.0, abs_tol=1e-9) else 1.0
            else:
                scale = objective_spec.scale_for_index(index, self._result_reference_scale(result, term.metric_key))
                contribution = objective_spec.normalized_weight(index) * (raw_value / scale)
            breakdown.append((METRIC_DEFINITIONS[term.metric_key].label, term.weight, raw_value, contribution))
        return breakdown

    def _result_reference_scale(self, result: BuildResult, metric_key: str) -> float:
        if metric_key == "hp_total":
            return max(1.0, float(result.gear_health_bonus))
        if metric_key == "effective_hp":
            return max(1.0, self._effective_hp_value(result.totals, result.effective_skills))
        if metric_key == "melee_avg":
            if result.weapon is None:
                return 1.0
            optimistic = {skill: max(result.base_skills.get(skill, 0), LEVEL_105_MAX_BASE_SKILL) + int(result.totals.get(skill, 0.0)) for skill in SKILLS}
            profiles = self._compute_damage_profiles(result.weapon, result.totals, optimistic)
            profile = profiles.get("Melee")
            return max(1.0, expected_average_from_profile(profile) if profile else 0.0)
        if metric_key == "spell_avg":
            if result.weapon is None:
                return 1.0
            optimistic = {skill: max(result.base_skills.get(skill, 0), LEVEL_105_MAX_BASE_SKILL) + int(result.totals.get(skill, 0.0)) for skill in SKILLS}
            profiles = self._compute_damage_profiles(result.weapon, result.totals, optimistic)
            profile = profiles.get("Spell")
            return max(1.0, expected_average_from_profile(profile) if profile else 0.0)
        return max(1.0, abs(float(result.totals.get(metric_key, 0.0))) or 1.0)


class BuildOptimizer:
    def __init__(self, engine: WynnBuildEngine) -> None:
        self.engine = engine
        self._objective: OptimizationObjective = make_optimization_objective((("hp_total", 1.0),))
        self._constraints: tuple[OptimizationConstraint, ...] = tuple()
        self._metric_keys_for_candidates: frozenset[str] = frozenset()
        self._group_order: list[str] = []
        self._group_candidates: list[list[GroupCandidate]] = []
        self._remaining_stat_maxima: list[dict[str, float]] = []
        self._remaining_set_piece_caps: list[dict[str, int]] = []
        self._remaining_melee_base: list[float] = []
        self._remaining_spell_base: list[float] = []
        self._group_stat_maxima: list[dict[str, float]] = []
        self._group_set_caps: list[dict[str, int]] = []
        self._all_stat_maxima: dict[str, float] = {}
        self._all_set_caps: dict[str, int] = {}
        self._all_melee_base: float = 0.0
        self._all_spell_base: float = 0.0
        self._reward_scale_hint: float = 1.0
        self._prepared_space_cache: dict[tuple[Any, ...], PreparedSearchSpace] = {}
        self._materialized_option_cache: dict[tuple[Any, ...], BuildOption] = {}
        self._base_slot_candidate_cache: dict[tuple[str, int | None], tuple[GroupCandidate, ...]] = {}
        self._filtered_ring_pair_cache: dict[tuple[Any, ...], tuple[GroupCandidate, ...]] = {}
        self._requirement_region_contains_cache: dict[
            tuple[
                tuple[tuple[int, int, int, int, int], ...],
                tuple[tuple[int, int, int, int, int], ...],
            ],
            bool,
        ] = {}

    def _prepared_search_cache_key(
        self,
        required_selections: dict[str, str],
        objective_metric: OptimizationObjective,
        constraints: list[OptimizationConstraint],
        max_combat_level: int | None,
    ) -> tuple[Any, ...]:
        return (
            selection_signature(required_selections),
            tuple(sorted({term.metric_key for term in objective_metric.terms})),
            tuple(sorted({constraint.metric_key for constraint in constraints})),
            None if max_combat_level is None else int(max_combat_level),
        )

    def _freeze_current_prepared_space(self, cache_id: tuple[Any, ...]) -> PreparedSearchSpace:
        return PreparedSearchSpace(
            cache_id=cache_id,
            metric_keys_for_candidates=self._metric_keys_for_candidates,
            group_order=tuple(self._group_order),
            group_candidates=tuple(tuple(candidate for candidate in candidates) for candidates in self._group_candidates),
            remaining_stat_maxima=tuple(dict(part) for part in self._remaining_stat_maxima),
            remaining_set_piece_caps=tuple(dict(part) for part in self._remaining_set_piece_caps),
            remaining_melee_base=tuple(self._remaining_melee_base),
            remaining_spell_base=tuple(self._remaining_spell_base),
            group_stat_maxima=tuple(dict(part) for part in self._group_stat_maxima),
            group_set_caps=tuple(dict(part) for part in self._group_set_caps),
            all_stat_maxima=dict(self._all_stat_maxima),
            all_set_caps=dict(self._all_set_caps),
            all_melee_base=self._all_melee_base,
            all_spell_base=self._all_spell_base,
        )

    def _load_prepared_space(self, prepared_space: PreparedSearchSpace) -> None:
        self._metric_keys_for_candidates = prepared_space.metric_keys_for_candidates
        self._group_order = list(prepared_space.group_order)
        self._group_candidates = [list(group) for group in prepared_space.group_candidates]
        self._remaining_stat_maxima = [dict(part) for part in prepared_space.remaining_stat_maxima]
        self._remaining_set_piece_caps = [dict(part) for part in prepared_space.remaining_set_piece_caps]
        self._remaining_melee_base = list(prepared_space.remaining_melee_base)
        self._remaining_spell_base = list(prepared_space.remaining_spell_base)
        self._group_stat_maxima = [dict(part) for part in prepared_space.group_stat_maxima]
        self._group_set_caps = [dict(part) for part in prepared_space.group_set_caps]
        self._all_stat_maxima = dict(prepared_space.all_stat_maxima)
        self._all_set_caps = dict(prepared_space.all_set_caps)
        self._all_melee_base = prepared_space.all_melee_base
        self._all_spell_base = prepared_space.all_spell_base

    def _activate_prepared_space(
        self,
        prepared_space: PreparedSearchSpace,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
    ) -> None:
        raw_objective = coerce_optimization_objective(objective_metric)
        self._objective = raw_objective
        self._constraints = tuple(constraints)
        self._load_prepared_space(prepared_space)
        self._materialized_option_cache = {}
        if raw_objective.is_single_metric():
            return
        root_state = SearchState(0, {}, tuple(), {}, {}, None, ((0, 0, 0, 0, 0),))
        scales = [
            max(1.0, abs(self._upper_bound_metric_for_state(root_state, term.metric_key)))
            for term in raw_objective.terms
        ]
        self._objective = raw_objective.with_scales(scales)

    def _prepare_search(
        self,
        required_selections: dict[str, str],
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        max_combat_level: int | None = None,
    ) -> PreparedSearchSpace:
        raw_objective = coerce_optimization_objective(objective_metric)
        cache_id = self._prepared_search_cache_key(required_selections, raw_objective, constraints, max_combat_level)
        prepared_space = self._prepared_space_cache.get(cache_id)
        if prepared_space is None:
            self._objective = raw_objective
            self._constraints = tuple(constraints)
            self._metric_keys_for_candidates = self._build_candidate_metric_keys(raw_objective, constraints)
            self._build_group_candidates(required_selections, max_combat_level)
            self._build_suffix_bounds()
            prepared_space = self._freeze_current_prepared_space(cache_id)
            self._prepared_space_cache[cache_id] = prepared_space
        self._activate_prepared_space(prepared_space, raw_objective, constraints)
        return prepared_space

    def generate(
        self,
        required_selections: dict[str, str],
        base_skills: dict[str, int] | None,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        top_n: int,
        max_combat_level: int | None = None,
        stop_event: threading.Event | None = None,
        progress_callback: Callable[[list[BuildOption], int, int, float, str], None] | None = None,
        summary_progress_callback: Callable[[list[SearchSolution], int, int, float, str], None] | None = None,
        prepared_space: PreparedSearchSpace | None = None,
    ) -> list[BuildOption]:
        if prepared_space is None:
            self._prepare_search(required_selections, objective_metric, constraints, max_combat_level)
        else:
            self._activate_prepared_space(prepared_space, objective_metric, constraints)

        started = time.perf_counter()
        next_progress = started + 0.6
        frontier: list[tuple[float, int, SearchState]] = []
        explored_states = 0
        sequence = 0
        root_state = SearchState(0, {}, tuple(), {}, {}, None, ((0, 0, 0, 0, 0),))
        self._reward_scale_hint = max(1.0, abs(self._upper_bound_for_state(root_state)))
        root_bound = self._upper_bound_for_state(root_state)
        heapq.heappush(frontier, (-root_bound, sequence, root_state))
        sequence += 1

        solutions: list[tuple[float, int, SearchSolution]] = []
        valid_signatures: set[tuple[str, ...]] = set()
        sequence = self._seed_initial_solutions(root_state, solutions, top_n, sequence, stop_event)
        if (progress_callback or summary_progress_callback) and solutions:
            valid_signatures.update(solution.selection_values for solution in self._sorted_solution_summaries(solutions))
            self._emit_progress(progress_callback, summary_progress_callback, solutions, explored_states, len(valid_signatures), started, "seeded initial results")
        if len(solutions) >= top_n:
            self._prune_candidates_against_score(solutions[0][0])
            self._build_suffix_bounds()
        frontier_buckets: defaultdict[tuple[Any, ...], list[SearchState]] = defaultdict(list)
        frontier_buckets[self._state_bucket(root_state)].append(root_state)

        while frontier:
            if stop_event and stop_event.is_set():
                break
            negative_bound, _order, state = heapq.heappop(frontier)
            explored_states += 1
            optimistic_bound = -negative_bound
            if not self._state_is_current(state, frontier_buckets):
                continue
            if len(solutions) >= top_n and optimistic_bound <= solutions[0][0]:
                break

            if state.group_index >= len(self._group_order):
                option = self._build_option_from_state(state)
                if option:
                    valid_signatures.add(option.selection_values)
                    if self._push_solution(solutions, option, top_n, sequence):
                        if len(solutions) >= top_n:
                            self._prune_candidates_against_score(solutions[0][0])
                            self._build_suffix_bounds()
                sequence += 1
            else:
                group_candidates = self._group_candidates[state.group_index]
                for candidate in group_candidates:
                    if stop_event and stop_event.is_set():
                        break
                    child = self._apply_candidate(state, candidate)
                    if not self._constraints_still_possible(child):
                        continue
                    child_bound = self._upper_bound_for_state(child)
                    if len(solutions) >= top_n and child_bound <= solutions[0][0]:
                        continue
                    if not self._register_state(child, frontier_buckets):
                        continue
                    heapq.heappush(frontier, (-child_bound, sequence, child))
                    sequence += 1

            if (progress_callback or summary_progress_callback) and time.perf_counter() >= next_progress:
                detail = f"explored {explored_states} states"
                if frontier:
                    detail += f", frontier {len(frontier)}"
                self._emit_progress(progress_callback, summary_progress_callback, solutions, explored_states, len(valid_signatures), started, detail)
                next_progress = time.perf_counter() + 0.6

        if progress_callback or summary_progress_callback:
            self._emit_progress(progress_callback, summary_progress_callback, solutions, explored_states, len(valid_signatures), started, f"finished after exploring {explored_states} states")
        return self._sorted_solution_options(solutions)

    def generate_mcts(
        self,
        required_selections: dict[str, str],
        base_skills: dict[str, int] | None,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        top_n: int,
        max_combat_level: int | None = None,
        stop_event: threading.Event | None = None,
        progress_callback: Callable[[list[BuildOption], int, int, float, str], None] | None = None,
        summary_progress_callback: Callable[[list[SearchSolution], int, int, float, str], None] | None = None,
        prepared_space: PreparedSearchSpace | None = None,
    ) -> list[BuildOption]:
        if prepared_space is None:
            self._prepare_search(required_selections, objective_metric, constraints, max_combat_level)
        else:
            self._activate_prepared_space(prepared_space, objective_metric, constraints)
        self._apply_mcts_candidate_caps()

        started = time.perf_counter()
        next_progress = started + 0.6
        iterations = 0
        sequence = 0
        solutions: list[tuple[float, int, SearchSolution]] = []
        valid_signatures: set[tuple[str, ...]] = set()
        root_state = SearchState(0, {}, tuple(), {}, {}, None, ((0, 0, 0, 0, 0),))
        self._reward_scale_hint = max(1.0, abs(self._upper_bound_for_state(root_state)))
        seed_attempts = [False, True, True, True, True, True]
        for randomized in seed_attempts:
            if stop_event and stop_event.is_set() and solutions:
                break
            if len(solutions) >= top_n:
                break
            _reward, option = self._greedy_complete_state(root_state, randomized=randomized)
            if option is None:
                continue
            valid_signatures.add(option.selection_values)
            self._push_solution(solutions, option, top_n, sequence)
            sequence += 1
        for _attempt in range(12):
            if stop_event and stop_event.is_set() and solutions:
                break
            if len(solutions) >= top_n:
                break
            _reward, option = self._rollout_from_state(root_state)
            if option is None:
                continue
            valid_signatures.add(option.selection_values)
            self._push_solution(solutions, option, top_n, sequence)
            sequence += 1

        if not self._group_order:
            option = self._build_option_from_state(root_state)
            if option:
                valid_signatures.add(option.selection_values)
                self._push_solution(solutions, option, top_n, sequence)
            if progress_callback or summary_progress_callback:
                self._emit_progress(progress_callback, summary_progress_callback, solutions, iterations, len(valid_signatures), started, "search complete")
            return self._sorted_solution_options(solutions)

        root = MCTSNode(
            state=root_state,
            parent=None,
            untried_indices=list(range(len(self._group_candidates[0]))),
        )

        while not (stop_event and stop_event.is_set()):
            if root.fully_explored:
                break

            node = self._select_mcts_node(root)
            if node.fully_explored and node is root:
                break

            if node.state.group_index < len(self._group_order) and node.untried_indices:
                expanded = self._expand_mcts_node(node)
                if expanded is not None:
                    node = expanded

            reward, option = self._rollout_from_state(node.state)
            if option is not None:
                valid_signatures.add(option.selection_values)
                self._push_solution(solutions, option, top_n, sequence)
                sequence += 1

            if node.state.group_index >= len(self._group_order):
                node.fully_explored = True

            self._backpropagate_reward(node, reward)
            self._mark_node_if_exhausted(node)
            iterations += 1

            if (progress_callback or summary_progress_callback) and time.perf_counter() >= next_progress:
                self._emit_progress(progress_callback, summary_progress_callback, solutions, iterations, len(valid_signatures), started, f"{iterations} iterations")
                next_progress = time.perf_counter() + 0.6

        if progress_callback or summary_progress_callback:
            detail = f"stopped after {iterations} iterations" if stop_event and stop_event.is_set() else f"finished after {iterations} iterations"
            self._emit_progress(progress_callback, summary_progress_callback, solutions, iterations, len(valid_signatures), started, detail)
        return self._sorted_solution_options(solutions)

    def estimate_exact_search(
        self,
        required_selections: dict[str, str],
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        top_n: int,
        max_combat_level: int | None = None,
        sample_time_budget: float = 0.45,
        sample_state_budget: int = 4000,
        prepared_space: PreparedSearchSpace | None = None,
    ) -> ExactSearchEstimate:
        setup_started = time.perf_counter()
        if prepared_space is None:
            self._prepare_search(required_selections, objective_metric, constraints, max_combat_level)
        else:
            self._activate_prepared_space(prepared_space, objective_metric, constraints)
        setup_elapsed = time.perf_counter() - setup_started
        candidate_group_sizes = tuple(len(candidates) for candidates in self._group_candidates)

        raw_total_states = 1
        product = 1
        for group_size in candidate_group_sizes:
            product *= max(1, group_size)
            raw_total_states += product

        if not self._group_order:
            return ExactSearchEstimate(
                estimated_seconds=setup_elapsed,
                low_seconds=setup_elapsed,
                high_seconds=setup_elapsed,
                states_per_second=0.0,
                sampled_states=0,
                estimated_total_states=1,
                raw_total_states=1,
                completed_during_sample=True,
                candidate_group_sizes=candidate_group_sizes,
            )

        search_started = time.perf_counter()
        frontier: list[tuple[float, int, SearchState]] = []
        explored_states = 0
        sequence = 0
        root_state = SearchState(0, {}, tuple(), {}, {}, None, ((0, 0, 0, 0, 0),))
        self._reward_scale_hint = max(1.0, abs(self._upper_bound_for_state(root_state)))
        root_bound = self._upper_bound_for_state(root_state)
        heapq.heappush(frontier, (-root_bound, sequence, root_state))
        sequence += 1

        solutions: list[tuple[float, int, SearchSolution]] = []
        sequence = self._seed_initial_solutions(root_state, solutions, top_n, sequence)
        if len(solutions) >= top_n:
            self._prune_candidates_against_score(solutions[0][0])
            self._build_suffix_bounds()
        frontier_buckets: defaultdict[tuple[Any, ...], list[SearchState]] = defaultdict(list)
        frontier_buckets[self._state_bucket(root_state)].append(root_state)

        depth_considered = [0 for _ in self._group_order]
        depth_registered = [0 for _ in self._group_order]
        completed_during_sample = False

        while frontier:
            elapsed = time.perf_counter() - search_started
            if elapsed >= sample_time_budget or explored_states >= sample_state_budget:
                break

            negative_bound, _order, state = heapq.heappop(frontier)
            explored_states += 1
            optimistic_bound = -negative_bound
            if not self._state_is_current(state, frontier_buckets):
                continue
            if len(solutions) >= top_n and optimistic_bound <= solutions[0][0]:
                completed_during_sample = True
                break

            if state.group_index >= len(self._group_order):
                option = self._build_option_from_state(state)
                if option and self._push_solution(solutions, option, top_n, sequence):
                    if len(solutions) >= top_n:
                        self._prune_candidates_against_score(solutions[0][0])
                        self._build_suffix_bounds()
                sequence += 1
                continue

            depth = state.group_index
            for candidate in self._group_candidates[depth]:
                depth_considered[depth] += 1
                child = self._apply_candidate(state, candidate)
                if not self._constraints_still_possible(child):
                    continue
                child_bound = self._upper_bound_for_state(child)
                if len(solutions) >= top_n and child_bound <= solutions[0][0]:
                    continue
                if not self._register_state(child, frontier_buckets):
                    continue
                depth_registered[depth] += 1
                heapq.heappush(frontier, (-child_bound, sequence, child))
                sequence += 1
        else:
            completed_during_sample = True

        search_elapsed = max(1e-9, time.perf_counter() - search_started)
        states_per_second = explored_states / search_elapsed if explored_states > 0 else 0.0

        if completed_during_sample:
            exact_seconds = setup_elapsed + search_elapsed
            return ExactSearchEstimate(
                estimated_seconds=exact_seconds,
                low_seconds=exact_seconds,
                high_seconds=exact_seconds,
                states_per_second=states_per_second,
                sampled_states=explored_states,
                estimated_total_states=max(1, explored_states),
                raw_total_states=raw_total_states,
                completed_during_sample=True,
                candidate_group_sizes=candidate_group_sizes,
            )

        total_considered = sum(depth_considered)
        total_registered = sum(depth_registered)
        global_survival = (total_registered / total_considered) if total_considered > 0 else 0.0
        estimated_states_by_depth = [1.0]
        for depth, group_size in enumerate(candidate_group_sizes):
            if depth_considered[depth] > 0:
                survival_ratio = depth_registered[depth] / depth_considered[depth]
            elif global_survival > 0.0:
                survival_ratio = global_survival
            else:
                survival_ratio = 1.0 / max(1, group_size)
            survival_ratio = max(0.0, min(1.0, survival_ratio))
            estimated_states_by_depth.append(estimated_states_by_depth[-1] * group_size * survival_ratio)

        estimated_total_states = max(
            explored_states,
            min(raw_total_states, int(round(sum(estimated_states_by_depth)))),
        )

        if states_per_second <= 0.0:
            estimated_seconds = setup_elapsed + search_elapsed
            uncertainty = 2.0
        else:
            estimated_seconds = setup_elapsed + (estimated_total_states / states_per_second)
            coverage = explored_states / max(1, estimated_total_states)
            if coverage >= 0.25:
                uncertainty = 0.35
            elif coverage >= 0.1:
                uncertainty = 0.6
            else:
                uncertainty = 1.0
            uncertainty = min(2.0, uncertainty + min(0.45, len(constraints) * 0.06))

        low_seconds = max(setup_elapsed, estimated_seconds / (1.0 + uncertainty))
        high_seconds = estimated_seconds * (1.0 + uncertainty)
        return ExactSearchEstimate(
            estimated_seconds=estimated_seconds,
            low_seconds=low_seconds,
            high_seconds=high_seconds,
            states_per_second=states_per_second,
            sampled_states=explored_states,
            estimated_total_states=estimated_total_states,
            raw_total_states=raw_total_states,
            completed_during_sample=False,
            candidate_group_sizes=candidate_group_sizes,
        )

    def _emit_progress(
        self,
        progress_callback: Callable[[list[BuildOption], int, int, float, str], None] | None,
        summary_progress_callback: Callable[[list[SearchSolution], int, int, float, str], None] | None,
        solutions: list[tuple[float, int, SearchSolution]],
        iterations: int,
        valid_count: int,
        started: float,
        detail: str,
    ) -> None:
        elapsed = time.perf_counter() - started
        summaries = self._sorted_solution_summaries(solutions)
        if summary_progress_callback is not None:
            summary_progress_callback(summaries, iterations, valid_count, elapsed, detail)
            return
        if progress_callback is not None:
            progress_callback(
                self._materialize_solution_options(summaries),
                iterations,
                valid_count,
                elapsed,
                detail,
            )

    def _build_option_from_state(self, state: SearchState) -> SearchSolution | None:
        selected_items = {
            slot_label: self.engine.item_lookup[label]
            for slot_label, label in state.selections.items()
            if label in self.engine.item_lookup
        }
        set_bonus_totals = self.engine.set_bonus_totals_from_counts(state.set_counts)
        totals = combine_dicts(state.item_totals, set_bonus_totals)
        weapon = self.engine.item_lookup.get(state.weapon_label) if state.weapon_label else None
        base_skill_dict = self.engine._optimize_level_105_base_skills_from_minima(
            state.req_minima,
            totals,
            weapon,
            self._objective,
            self._constraints,
        )
        if base_skill_dict is None:
            return None
        equip_order = self.engine._find_equip_order(selected_items, base_skill_dict)
        if equip_order is None:
            return None
        allocation = skill_dict_to_tuple(base_skill_dict)

        constraint_values: list[tuple[str, float]] = []
        for constraint in self._constraints:
            value = self.engine._metric_value_from_parts(constraint.metric_key, totals, weapon, allocation)
            constraint_values.append((constraint.display_label(), value))
            if not self._constraint_matches(value, constraint):
                return None

        score = self.engine.objective_value_from_parts(totals, weapon, allocation, self._objective)
        return SearchSolution(
            score=score,
            objective_value=score,
            selection_values=selection_signature(state.selections),
            base_skills=allocation,
            equip_order=tuple(equip_order),
            constraint_values=tuple(constraint_values),
        )

    def _evaluate_state(self, state: SearchState) -> tuple[float, SearchSolution | None]:
        solution = self._build_option_from_state(state)
        if solution is None:
            return -1005.0, None
        return solution.score, solution

    @staticmethod
    def _selection_signature(selections: dict[str, str]) -> tuple[str, ...]:
        return selection_signature(selections)

    @staticmethod
    def _solution_signature(solution: SearchSolution) -> tuple[str, ...]:
        return solution.selection_values

    def _materialize_option(self, solution: SearchSolution) -> BuildOption:
        cache_key = (
            solution.selection_values,
            solution.base_skills,
            tuple((term.metric_key, term.weight) for term in self._objective.terms),
            tuple(self._objective.scales),
            tuple((constraint.metric_key, constraint.operator, constraint.target) for constraint in self._constraints),
        )
        cached = self._materialized_option_cache.get(cache_key)
        if cached is not None:
            return cached
        result = self.engine.build_result_from_solution(solution, self._objective)
        option = BuildOption(
            score=solution.score,
            selections=solution.selections_dict(),
            result=result,
            objective_label=self._objective.display_label(),
            objective_value=solution.objective_value,
            objective=self._objective,
            constraint_values=dict(solution.constraint_values),
        )
        self._materialized_option_cache[cache_key] = option
        return option

    def _materialize_solution_options(self, solutions: list[SearchSolution]) -> list[BuildOption]:
        return [self._materialize_option(solution) for solution in solutions]

    def _push_solution(
        self,
        solutions: list[tuple[float, int, SearchSolution]],
        option: SearchSolution,
        top_n: int,
        sequence: int,
    ) -> bool:
        signature = self._solution_signature(option)
        for index, (_score, _order, existing_option) in enumerate(solutions):
            if self._solution_signature(existing_option) != signature:
                continue
            if option.score <= existing_option.score:
                return False
            solutions[index] = (option.score, sequence, option)
            heapq.heapify(solutions)
            return True

        if len(solutions) < top_n:
            heapq.heappush(solutions, (option.score, sequence, option))
            return True
        if option.score > solutions[0][0]:
            heapq.heapreplace(solutions, (option.score, sequence, option))
            return True
        return False

    @staticmethod
    def _sorted_solution_summaries(solutions: list[tuple[float, int, SearchSolution]]) -> list[SearchSolution]:
        return [entry[2] for entry in sorted(solutions, key=lambda row: row[0], reverse=True)]

    def _sorted_solution_options(self, solutions: list[tuple[float, int, SearchSolution]]) -> list[BuildOption]:
        return self._materialize_solution_options(self._sorted_solution_summaries(solutions))

    @staticmethod
    def _constraint_matches(value: float, constraint: OptimizationConstraint) -> bool:
        if constraint.operator == ">":
            return value > constraint.target
        if constraint.operator == "<":
            return value < constraint.target
        if constraint.operator == "=":
            return math.isclose(value, constraint.target, rel_tol=1e-9, abs_tol=1e-6)
        raise ValueError(f"Unsupported constraint operator: {constraint.operator}")

    @staticmethod
    def _constraint_penalty(value: float, constraint: OptimizationConstraint) -> float:
        scale = max(1.0, abs(constraint.target))
        if constraint.operator == ">":
            return max(0.0, constraint.target - value) / scale
        if constraint.operator == "<":
            return max(0.0, value - constraint.target) / scale
        if constraint.operator == "=":
            return abs(value - constraint.target) / scale
        return 1.0

    def _prune_candidates_against_score(self, cutoff_score: float) -> None:
        pruned_candidates: list[list[GroupCandidate]] = []
        for group_index, candidates in enumerate(self._group_candidates):
            kept: list[GroupCandidate] = []
            for candidate in candidates:
                upper_totals = dict(candidate.totals)
                group_maxima = self._group_stat_maxima[group_index]
                for key, value in self._all_stat_maxima.items():
                    upper_totals[key] = upper_totals.get(key, 0.0) + (value - group_maxima.get(key, 0.0))

                set_bonus_bound = self._optimistic_set_bonus_for_candidate(group_index, candidate)
                for key, value in set_bonus_bound.items():
                    upper_totals[key] = upper_totals.get(key, 0.0) + value

                if not self._candidate_constraints_possible(group_index, candidate, upper_totals):
                    continue
                upper_score = self._candidate_objective_upper_bound(group_index, candidate, upper_totals)
                if upper_score > cutoff_score:
                    kept.append(candidate)
            pruned_candidates.append(kept or candidates[:1])
        self._group_candidates = pruned_candidates

    def _optimistic_set_bonus_for_candidate(self, group_index: int, candidate: GroupCandidate) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)
        all_set_names = set(self._all_set_caps) | set(candidate.set_counts)
        for set_name in all_set_names:
            current = candidate.set_counts.get(set_name, 0)
            remaining = self._all_set_caps.get(set_name, 0) - self._group_set_caps[group_index].get(set_name, 0)
            max_count = min(current + max(0, remaining), len(self.engine.sets.get(set_name, {}).get("items", [])))
            for key, value in self.engine.set_bonus_for_count(set_name, max_count).items():
                totals[key] += value
        return dict(totals)

    def _candidate_constraints_possible(
        self,
        group_index: int,
        candidate: GroupCandidate,
        upper_totals: dict[str, float],
    ) -> bool:
        for constraint in self._constraints:
            if not self._constraint_possible_from_upper_bound(
                self._candidate_metric_upper_bound(group_index, candidate, upper_totals, constraint.metric_key),
                constraint,
            ):
                return False
        return True

    def _candidate_metric_upper_bound(
        self,
        group_index: int,
        candidate: GroupCandidate,
        upper_totals: dict[str, float],
        metric_key: str,
    ) -> float:
        if metric_key == "hp_total":
            return upper_totals.get("hp", 0.0) + upper_totals.get("hpBonus", 0.0)
        if metric_key == "effective_hp":
            return self._effective_hp_upper_bound(upper_totals, candidate.req_minima)
        if metric_key == "melee_avg":
            base_total = candidate.totals.get(PSEUDO_MELEE_BASE, 0.0) or self._all_melee_base
            return self._damage_metric_upper_bound(base_total, upper_totals, "melee", candidate.req_minima)
        if metric_key == "spell_avg":
            base_total = candidate.totals.get(PSEUDO_SPELL_BASE, 0.0) or self._all_spell_base
            return self._damage_metric_upper_bound(base_total, upper_totals, "spell", candidate.req_minima)
        if metric_key in SKILLS:
            allocation = self._optimistic_base_allocation(candidate.req_minima, metric_key)
            return upper_totals.get(metric_key, 0.0) + allocation[SKILLS.index(metric_key)]
        return upper_totals.get(metric_key, 0.0)

    def _seed_initial_solutions(
        self,
        state: SearchState,
        solutions: list[tuple[float, int, SearchSolution]],
        top_n: int,
        sequence_start: int,
        stop_event: threading.Event | None = None,
    ) -> int:
        sequence = sequence_start
        seed_attempts = [False, True, True, True, True, True]
        for randomized in seed_attempts:
            if stop_event and stop_event.is_set():
                break
            if len(solutions) >= top_n:
                break
            _reward, option = self._greedy_complete_state(state, randomized=randomized)
            if option is None:
                continue
            self._push_solution(solutions, option, top_n, sequence)
            sequence += 1

        rollout_attempts = max(8, min(24, top_n * 6))
        for _attempt in range(rollout_attempts):
            if stop_event and stop_event.is_set():
                break
            if len(solutions) >= top_n:
                break
            _reward, option = self._rollout_from_state(state)
            if option is None:
                continue
            self._push_solution(solutions, option, top_n, sequence)
            sequence += 1
        return sequence

    def _build_candidate_metric_keys(
        self,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
    ) -> frozenset[str]:
        objective = coerce_optimization_objective(objective_metric)
        keys = set(SKILLS)
        for term in objective.terms:
            keys.update(METRIC_DEFINITIONS[term.metric_key].relevant_keys)
        for constraint in constraints:
            keys.update(METRIC_DEFINITIONS[constraint.metric_key].relevant_keys)
        return frozenset(keys)

    def _objective_family(self) -> str:
        if any(
            term.metric_key in {"melee_avg", "spell_avg"}
            for term in self._objective.terms
        ) or any(
            constraint.metric_key in {"melee_avg", "spell_avg"}
            for constraint in self._constraints
        ):
            return "damage"
        return "stat"

    def _raw_total_state_estimate(self) -> int:
        raw_total_states = 1
        product = 1
        for candidates in self._group_candidates:
            product *= max(1, len(candidates))
            raw_total_states += product
        return raw_total_states

    def _apply_mcts_candidate_caps(self) -> None:
        if not self._group_candidates:
            return
        if self._raw_total_state_estimate() <= MCTS_UNCAPPED_STATE_THRESHOLD:
            return

        capped_groups: list[list[GroupCandidate]] = []
        changed = False
        for group_name, candidates in zip(self._group_order, self._group_candidates):
            cap = GROUP_CANDIDATE_CAPS.get(group_name)
            if cap is None or len(candidates) <= cap:
                capped_groups.append(candidates)
                continue
            capped_groups.append(sorted(candidates, key=self._candidate_sort_key, reverse=True)[:cap])
            changed = True

        if not changed:
            return
        self._group_candidates = capped_groups
        self._build_suffix_bounds()

    @staticmethod
    def _metric_vector_dominates(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
        strictly_better = False
        for left_value, right_value in zip(left, right):
            if left_value < right_value:
                return False
            if left_value > right_value:
                strictly_better = True
        return strictly_better

    def _base_slot_candidates(
        self,
        slot_label: str,
        max_combat_level: int | None,
    ) -> list[GroupCandidate]:
        cache_key = (slot_label, None if max_combat_level is None else int(max_combat_level))
        cached = self._base_slot_candidate_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        base_candidates = tuple(
            self._make_candidate_from_facts(
                slot_label,
                {slot_label: fact.label},
                (fact,),
                pack_for_search=False,
            )
            for fact in self.engine.slot_candidate_facts_for_level(slot_label, max_combat_level)
        )
        self._base_slot_candidate_cache[cache_key] = base_candidates
        return list(base_candidates)

    def _reduce_same_requirement_candidates(
        self,
        candidates: list[GroupCandidate],
    ) -> list[GroupCandidate]:
        ordered = sorted(candidates, key=lambda candidate: candidate.sort_vector, reverse=True)
        kept: list[GroupCandidate] = []
        seen_vectors: set[tuple[float, ...]] = set()
        for candidate in ordered:
            if candidate.metric_vector in seen_vectors:
                continue
            dominated = False
            index = 0
            while index < len(kept):
                other = kept[index]
                if self._metric_vector_dominates(other.metric_vector, candidate.metric_vector):
                    dominated = True
                    break
                if self._metric_vector_dominates(candidate.metric_vector, other.metric_vector):
                    kept.pop(index)
                else:
                    index += 1
            if not dominated:
                kept.append(candidate)
                seen_vectors.add(candidate.metric_vector)
        return kept

    @staticmethod
    def _requirement_region_sort_key(
        req_packed: tuple[tuple[int, int, int, int, int], ...],
    ) -> tuple[Any, ...]:
        minima_sums = tuple(sum(values) for values in req_packed)
        return (
            min(minima_sums, default=0),
            len(req_packed),
            minima_sums,
            req_packed,
        )

    def _cached_requirement_region_contains(
        self,
        left_minima: tuple[tuple[int, int, int, int, int], ...],
        right_minima: tuple[tuple[int, int, int, int, int], ...],
    ) -> bool:
        cache_key = (left_minima, right_minima)
        cached = self._requirement_region_contains_cache.get(cache_key)
        if cached is not None:
            return cached
        if len(left_minima) == 1:
            left = left_minima[0]
            if len(right_minima) == 1:
                right = right_minima[0]
                result = all(left[i] <= right[i] for i in range(5))
            else:
                result = True
                for right in right_minima:
                    if any(left[i] > right[i] for i in range(5)):
                        result = False
                        break
        else:
            result = True
            for right in right_minima:
                matched = False
                for left in left_minima:
                    if all(left[i] <= right[i] for i in range(5)):
                        matched = True
                        break
                if not matched:
                    result = False
                    break
        self._requirement_region_contains_cache[cache_key] = result
        return result

    def _build_ring_pair_frontier(
        self,
        ring_candidates: list[GroupCandidate],
    ) -> list[GroupCandidate]:
        ring_labels = tuple(candidate.item_labels[0] for candidate in ring_candidates)
        cache_key = (
            ring_labels,
            tuple(sorted(self._metric_keys_for_candidates)),
        )
        cached = self._filtered_ring_pair_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        pair_candidates: list[GroupCandidate] = []
        for index, left_candidate in enumerate(ring_candidates):
            left_label = left_candidate.item_labels[0]
            left_fact = self.engine.item_fact_lookup[left_label]
            for right_candidate in ring_candidates[index:]:
                right_label = right_candidate.item_labels[0]
                right_fact = self.engine.item_fact_lookup[right_label]
                pair_candidates.append(
                    self._make_candidate_from_facts(
                        "Rings",
                        {"Ring 1": left_label, "Ring 2": right_label},
                        (left_fact, right_fact),
                        pack_for_search=False,
                    )
                )

        filtered = tuple(self._filter_group_candidates(pair_candidates))
        self._filtered_ring_pair_cache[cache_key] = filtered
        return list(filtered)

    def _build_group_candidates(self, required_selections: dict[str, str], max_combat_level: int | None = None) -> None:
        filtered_singletons: dict[str, list[GroupCandidate]] = {}
        damage_involved = self._objective_family() == "damage"

        for slot_label, _slot_type in SLOT_CONFIGS:
            if slot_label in {"Ring 1", "Ring 2"}:
                continue
            required_label = required_selections.get(slot_label, "").strip()
            if required_label:
                fact = self.engine.item_fact_lookup.get(required_label)
                if fact is None:
                    raise ValueError(f"Unknown required item for {slot_label}: {required_label}")
                if max_combat_level is not None and fact.level_requirement > int(max_combat_level):
                    raise ValueError(
                        f"{required_label} requires combat level {fact.level_requirement}, above the current filter of {int(max_combat_level)}."
                    )
                filtered_singletons[slot_label] = [
                    self._make_candidate_from_facts(slot_label, {slot_label: fact.label}, (fact,))
                ]
            else:
                base_candidates = self._base_slot_candidates(slot_label, max_combat_level)
                filtered_singletons[slot_label] = self._filter_group_candidates(base_candidates)

        ring_candidates = self._filter_group_candidates(self._base_slot_candidates("Ring 1", max_combat_level))
        ring1_required = required_selections.get("Ring 1", "").strip()
        ring2_required = required_selections.get("Ring 2", "").strip()

        group_candidates: dict[str, list[GroupCandidate]] = {
            slot_label: list(filtered_singletons[slot_label])
            for slot_label in ("Helmet", "Chestplate", "Pants", "Boots", "Bracelet", "Necklace", "Weapon")
        }

        ring_pairs: list[GroupCandidate] = []
        if ring1_required and ring2_required:
            fact1 = self.engine.item_fact_lookup.get(ring1_required)
            fact2 = self.engine.item_fact_lookup.get(ring2_required)
            if fact1 is None or fact2 is None:
                missing = ring1_required if fact1 is None else ring2_required
                raise ValueError(f"Unknown required ring: {missing}")
            if max_combat_level is not None and (
                fact1.level_requirement > int(max_combat_level) or fact2.level_requirement > int(max_combat_level)
            ):
                raise ValueError(
                    f"Required rings must be at or below combat level {int(max_combat_level)}."
                )
            ring_pairs = [self._make_candidate_from_facts("Rings", {"Ring 1": ring1_required, "Ring 2": ring2_required}, (fact1, fact2))]
        elif ring1_required or ring2_required:
            fixed_slot = "Ring 1" if ring1_required else "Ring 2"
            open_slot = "Ring 2" if fixed_slot == "Ring 1" else "Ring 1"
            fixed_item = self.engine.item_fact_lookup.get(ring1_required or ring2_required)
            if fixed_item is None:
                raise ValueError(f"Unknown required ring: {ring1_required or ring2_required}")
            if max_combat_level is not None and fixed_item.level_requirement > int(max_combat_level):
                raise ValueError(
                    f"{fixed_item.label} requires combat level {fixed_item.level_requirement}, above the current filter of {int(max_combat_level)}."
                )
            for ring in ring_candidates:
                ring_label = ring.item_labels[0]
                ring_fact = self.engine.item_fact_lookup[ring_label]
                ring_pairs.append(
                    self._make_candidate_from_facts(
                        "Rings",
                        {fixed_slot: fixed_item.label, open_slot: ring_label},
                        (fixed_item, ring_fact),
                    )
                )
        else:
            ring_pairs = self._build_ring_pair_frontier(ring_candidates)
        group_candidates["Rings"] = self._filter_group_candidates(ring_pairs) if ring1_required or ring2_required else ring_pairs

        ordered_names = ["Weapon"] if damage_involved else []
        for slot_label in ("Helmet", "Chestplate", "Pants", "Boots", "Rings", "Bracelet", "Necklace", "Weapon"):
            if slot_label not in ordered_names:
                ordered_names.append(slot_label)
        ordered_names.sort(key=lambda name: (0 if name == "Weapon" and damage_involved else 1, len(group_candidates[name]), name))

        self._group_order = ordered_names
        self._group_candidates = [
            sorted(group_candidates[name], key=self._candidate_sort_key, reverse=True)
            for name in self._group_order
        ]

    def _make_candidate_from_facts(
        self,
        group_name: str,
        selections: dict[str, str],
        items: tuple[CandidateFact, ...],
        pack_for_search: bool = True,
    ) -> GroupCandidate:
        totals = combine_dicts(*(item.totals for item in items))
        set_counts: Counter[str] = Counter()
        item_labels = tuple(sorted(item.label for item in items))
        req_minima = self._requirement_minima_for_labels(item_labels)

        for item in items:
            if item.set_name:
                set_counts[item.set_name] += 1

        weapon_label = None
        for item in items:
            if item.category == "weapon":
                weapon_label = item.label
                totals[PSEUDO_MELEE_BASE] = item.melee_base
                totals[PSEUDO_SPELL_BASE] = item.spell_base
                break

        candidate = GroupCandidate(
            group_name=group_name,
            selections=dict(selections),
            item_labels=item_labels,
            totals=totals,
            set_counts=dict(set_counts),
            req_minima=req_minima,
            weapon_label=weapon_label,
        )
        return self._pack_candidate_for_search(candidate) if pack_for_search else candidate

    def _pack_candidate_for_search(self, candidate: GroupCandidate) -> GroupCandidate:
        metric_keys = tuple(sorted(self._metric_keys_for_candidates))
        metric_vector = tuple(candidate.totals.get(key, 0.0) for key in metric_keys)
        req_packed = tuple(sorted(candidate.req_minima))
        return GroupCandidate(
            group_name=candidate.group_name,
            selections=candidate.selections,
            item_labels=candidate.item_labels,
            totals=candidate.totals,
            set_counts=candidate.set_counts,
            req_minima=candidate.req_minima,
            weapon_label=candidate.weapon_label,
            metric_vector=metric_vector,
            sort_vector=(sum(metric_vector),) + metric_vector,
            req_packed=req_packed,
        )

    def _filter_group_candidates(
        self,
        candidates: list[GroupCandidate],
        keep_placeholder_slot: bool = False,
    ) -> list[GroupCandidate]:
        if len(candidates) <= 1:
            return [self._pack_candidate_for_search(candidate) for candidate in candidates]

        buckets: defaultdict[tuple[Any, ...], list[GroupCandidate]] = defaultdict(list)
        for candidate in candidates:
            set_signature = tuple(sorted(candidate.set_counts.items()))
            weapon_type = None
            if candidate.weapon_label:
                weapon_type = self.engine.item_lookup[candidate.weapon_label].get("type")
            buckets[(set_signature, weapon_type)].append(candidate)

        survivors: list[GroupCandidate] = []
        for bucket_candidates in buckets.values():
            packed_candidates = [self._pack_candidate_for_search(candidate) for candidate in bucket_candidates]
            by_requirements: defaultdict[tuple[tuple[int, int, int, int, int], ...], list[GroupCandidate]] = defaultdict(list)
            for candidate in packed_candidates:
                by_requirements[candidate.req_packed].append(candidate)

            reduced_by_requirements = {
                req_packed: self._reduce_same_requirement_candidates(group_candidates)
                for req_packed, group_candidates in by_requirements.items()
            }
            simple_requirements: dict[tuple[int, int, int, int, int], list[GroupCandidate]] = {}
            complex_requirements: dict[tuple[tuple[int, int, int, int, int], ...], list[GroupCandidate]] = {}
            for req_packed, reduced_candidates in reduced_by_requirements.items():
                if len(req_packed) == 1:
                    simple_requirements[req_packed[0]] = reduced_candidates
                else:
                    complex_requirements[req_packed] = reduced_candidates

            accepted_simple: list[tuple[tuple[int, int, int, int, int], GroupCandidate]] = []
            for req_tuple in sorted(
                simple_requirements,
                key=lambda values: (sum(values), values),
            ):
                accepted: list[GroupCandidate] = []
                for candidate in simple_requirements[req_tuple]:
                    dominated = False
                    for other_req, other in accepted_simple:
                        if any(other_req[index] > req_tuple[index] for index in range(5)):
                            continue
                        if self._metric_vector_dominates(other.metric_vector, candidate.metric_vector):
                            dominated = True
                            break
                    if not dominated:
                        accepted.append(candidate)
                if accepted:
                    survivors.extend(accepted)
                    accepted_simple.extend((req_tuple, candidate) for candidate in accepted)

            accepted_complex: list[tuple[tuple[tuple[int, int, int, int, int], ...], GroupCandidate]] = []
            for req_packed in sorted(complex_requirements, key=self._requirement_region_sort_key):
                accepted: list[GroupCandidate] = []
                for candidate in complex_requirements[req_packed]:
                    dominated = False
                    for other_req, other in accepted_simple:
                        if self._cached_requirement_region_contains((other_req,), req_packed) and self._metric_vector_dominates(
                            other.metric_vector,
                            candidate.metric_vector,
                        ):
                            dominated = True
                            break
                    if dominated:
                        continue
                    for other_req, other in accepted_complex:
                        if self._cached_requirement_region_contains(other_req, req_packed) and self._metric_vector_dominates(
                            other.metric_vector,
                            candidate.metric_vector,
                        ):
                            dominated = True
                            break
                    if not dominated:
                        accepted.append(candidate)
                if accepted:
                    survivors.extend(accepted)
                    accepted_complex.extend((req_packed, candidate) for candidate in accepted)

        if keep_placeholder_slot:
            return survivors
        return [candidate for candidate in survivors if candidate.selections]

    def _candidate_dominates(self, left: GroupCandidate, right: GroupCandidate) -> bool:
        left_req = left.req_packed or tuple(sorted(left.req_minima))
        right_req = right.req_packed or tuple(sorted(right.req_minima))
        if not self._cached_requirement_region_contains(left_req, right_req):
            return False
        left_vector = left.metric_vector or tuple(left.totals.get(key, 0.0) for key in sorted(self._metric_keys_for_candidates))
        right_vector = right.metric_vector or tuple(right.totals.get(key, 0.0) for key in sorted(self._metric_keys_for_candidates))
        if not self._metric_vector_dominates(left_vector, right_vector):
            return False
        if left_req == right_req:
            return False
        return True

    def _state_bucket(self, state: SearchState) -> tuple[Any, ...]:
        return (
            state.group_index,
            state.weapon_label or "",
            tuple(sorted(state.set_counts.items())),
        )

    def _state_dominates(self, left: SearchState, right: SearchState) -> bool:
        if not self._cached_requirement_region_contains(left.req_minima, right.req_minima):
            return False
        strictly_better = False
        for key in self._metric_keys_for_candidates:
            left_value = left.item_totals.get(key, 0.0)
            right_value = right.item_totals.get(key, 0.0)
            if left_value < right_value:
                return False
            if left_value > right_value:
                strictly_better = True
        if not strictly_better and left.req_minima == right.req_minima:
            return False
        return True

    def _state_is_current(
        self,
        state: SearchState,
        buckets: defaultdict[tuple[Any, ...], list[SearchState]],
    ) -> bool:
        return any(existing is state for existing in buckets[self._state_bucket(state)])

    def _register_state(
        self,
        state: SearchState,
        buckets: defaultdict[tuple[Any, ...], list[SearchState]],
    ) -> bool:
        bucket_key = self._state_bucket(state)
        existing_states = buckets[bucket_key]
        for existing in existing_states:
            if self._state_dominates(existing, state):
                return False

        buckets[bucket_key] = [
            existing
            for existing in existing_states
            if not self._state_dominates(state, existing)
        ]
        buckets[bucket_key].append(state)
        return True

    def _select_mcts_node(self, root: MCTSNode) -> MCTSNode:
        node = root
        while True:
            if node.state.group_index >= len(self._group_order):
                return node
            if node.untried_indices:
                return node

            open_children = [child for child in node.children if not child.fully_explored]
            if not open_children:
                node.fully_explored = True
                self._mark_node_if_exhausted(node)
                return node

            node = max(open_children, key=lambda child: self._mcts_child_score(child, node.visits))

    def _mcts_child_score(self, child: MCTSNode, parent_visits: int) -> float:
        if child.visits <= 0:
            return float("inf")

        mean_reward = (child.total_reward / child.visits) / self._reward_scale_hint
        best_reward = max(0.0, child.best_reward) / self._reward_scale_hint
        exploration = 1.15 * math.sqrt(math.log(max(2, parent_visits)) / child.visits)
        return mean_reward + (0.08 * best_reward) + exploration

    def _expand_mcts_node(self, node: MCTSNode) -> MCTSNode | None:
        while node.untried_indices:
            candidate_index = self._pop_biased_index(node.untried_indices)
            candidate = self._group_candidates[node.state.group_index][candidate_index]
            child_state = self._apply_candidate(node.state, candidate)
            if not self._constraints_still_possible(child_state):
                continue

            child_untried: list[int] = []
            if child_state.group_index < len(self._group_order):
                child_untried = list(range(len(self._group_candidates[child_state.group_index])))
            child = MCTSNode(
                state=child_state,
                parent=node,
                untried_indices=child_untried,
            )
            node.children.append(child)
            return child

        self._mark_node_if_exhausted(node)
        return None

    @staticmethod
    def _pop_biased_index(indices: list[int]) -> int:
        if len(indices) == 1:
            return indices.pop()

        favored_window = min(12, len(indices))
        if random.random() < 0.78:
            pick_index = min(favored_window - 1, int((random.random() ** 2) * favored_window))
        else:
            pick_index = random.randrange(len(indices))
        return indices.pop(pick_index)

    def _rollout_from_state(self, state: SearchState) -> tuple[float, SearchSolution | None]:
        current = state
        while current.group_index < len(self._group_order):
            candidates = self._group_candidates[current.group_index]
            sampled_indices = self._sample_rollout_indices(len(candidates))
            viable_children: list[tuple[SearchState, float]] = []
            seen_indices = set(sampled_indices)

            for candidate_index in sampled_indices:
                child = self._apply_candidate(current, candidates[candidate_index])
                if not self._constraints_still_possible(child):
                    continue
                viable_children.append((child, self._upper_bound_for_state(child) - self._feasibility_penalty(child.req_minima)))

            if not viable_children and len(seen_indices) < len(candidates):
                for candidate_index, candidate in enumerate(candidates):
                    if candidate_index in seen_indices:
                        continue
                    child = self._apply_candidate(current, candidate)
                    if not self._constraints_still_possible(child):
                        continue
                    viable_children.append((child, self._upper_bound_for_state(child) - self._feasibility_penalty(child.req_minima)))
                    if len(viable_children) >= 6:
                        break

            if not viable_children:
                missing_groups = len(self._group_order) - current.group_index
                return (-1000.0 - float(missing_groups)), None

            current = self._choose_rollout_child(viable_children)

        return self._evaluate_state(current)

    def _greedy_complete_state(self, state: SearchState, randomized: bool = False) -> tuple[float, SearchSolution | None]:
        current = state
        while current.group_index < len(self._group_order):
            candidates = self._group_candidates[current.group_index]
            if randomized:
                candidate_indices = self._sample_rollout_indices(len(candidates))
            else:
                candidate_indices = list(range(min(40, len(candidates))))

            best_child: SearchState | None = None
            best_rank: tuple[float, float, float] | None = None
            seen_indices = set(candidate_indices)

            for candidate_index in candidate_indices:
                child = self._apply_candidate(current, candidates[candidate_index])
                if not self._constraints_still_possible(child):
                    continue
                shortfall = float(self._base_skill_shortfall(child.req_minima))
                score = self._upper_bound_for_state(child)
                tie_break = random.random() if randomized else float(candidate_index)
                rank = (shortfall, -score, tie_break)
                if best_rank is None or rank < best_rank:
                    best_rank = rank
                    best_child = child

            if best_child is None and len(seen_indices) < len(candidates):
                for candidate_index, candidate in enumerate(candidates):
                    if candidate_index in seen_indices:
                        continue
                    child = self._apply_candidate(current, candidate)
                    if not self._constraints_still_possible(child):
                        continue
                    shortfall = float(self._base_skill_shortfall(child.req_minima))
                    score = self._upper_bound_for_state(child)
                    rank = (shortfall, -score, float(candidate_index))
                    if best_rank is None or rank < best_rank:
                        best_rank = rank
                        best_child = child

            if best_child is None:
                missing_groups = len(self._group_order) - current.group_index
                return (-1000.0 - float(missing_groups)), None

            current = best_child

        return self._evaluate_state(current)

    @staticmethod
    def _sample_rollout_indices(candidate_count: int) -> list[int]:
        if candidate_count <= 24:
            return list(range(candidate_count))

        chosen = list(range(min(10, candidate_count)))
        chosen_set = set(chosen)
        while len(chosen) < 24:
            candidate_index = random.randrange(candidate_count)
            if candidate_index in chosen_set:
                continue
            chosen.append(candidate_index)
            chosen_set.add(candidate_index)
        return chosen

    @staticmethod
    def _choose_rollout_child(scored_children: list[tuple[SearchState, float]]) -> SearchState:
        scored_children.sort(key=lambda entry: entry[1], reverse=True)
        if len(scored_children) == 1 or random.random() < 0.68:
            return scored_children[0][0]

        top_window = min(6, len(scored_children))
        choices = [child for child, _score in scored_children[:top_window]]
        weights = [top_window - index for index in range(top_window)]
        return random.choices(choices, weights=weights, k=1)[0]

    @staticmethod
    def _backpropagate_reward(node: MCTSNode, reward: float) -> None:
        current: MCTSNode | None = node
        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current.best_reward = max(current.best_reward, reward)
            current = current.parent

    def _mark_node_if_exhausted(self, node: MCTSNode) -> None:
        current: MCTSNode | None = node
        while current is not None:
            if current.state.group_index >= len(self._group_order):
                current.fully_explored = True
            else:
                current.fully_explored = (not current.untried_indices) and all(child.fully_explored for child in current.children)
            if not current.fully_explored:
                break
            current = current.parent

    @lru_cache(maxsize=None)
    def _requirement_minima_for_labels(
        self,
        item_labels: tuple[str, ...],
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        return self.engine.requirement_minima_for_labels(item_labels)

    def _requirement_minima_for_items(
        self,
        items: tuple[dict[str, Any], ...],
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        return self.engine._requirement_minima_for_items(items)

    def _candidate_sort_key(self, candidate: GroupCandidate) -> float:
        if self._objective.is_single_metric():
            metric = self._objective.primary_metric_key()
            return self._candidate_metric_sort_value(candidate, metric) - self._feasibility_penalty(candidate.req_minima)

        score = 0.0
        for index, term in enumerate(self._objective.terms):
            raw_value = self._candidate_metric_sort_value(candidate, term.metric_key)
            scale = self._objective.scale_for_index(index, raw_value)
            score += self._objective.normalized_weight(index) * (raw_value / scale)
        return score - self._feasibility_penalty(candidate.req_minima)

    def _candidate_metric_sort_value(self, candidate: GroupCandidate, metric: str) -> float:
        if metric == "hp_total":
            return candidate.totals.get("hp", 0.0) + candidate.totals.get("hpBonus", 0.0)
        if metric == "effective_hp":
            return self._effective_hp_upper_bound(candidate.totals, candidate.req_minima)
        if metric == "melee_avg":
            return candidate.totals.get(PSEUDO_MELEE_BASE, 0.0) + candidate.totals.get("mdPct", 0.0) + candidate.totals.get("damPct", 0.0)
        if metric == "spell_avg":
            return candidate.totals.get(PSEUDO_SPELL_BASE, 0.0) + candidate.totals.get("sdPct", 0.0) + candidate.totals.get("damPct", 0.0)
        return candidate.totals.get(metric, 0.0)

    def _base_skill_shortfall(self, req_minima: tuple[tuple[int, int, int, int, int], ...]) -> int:
        if not req_minima:
            return 0

        return min(
            level_105_allocation_shortfall(minima)
            for minima in req_minima
        )

    def _feasibility_penalty(self, req_minima: tuple[tuple[int, int, int, int, int], ...]) -> float:
        shortfall = self._base_skill_shortfall(req_minima)
        return shortfall * max(150.0, self._reward_scale_hint / 35.0)

    def _build_suffix_bounds(self) -> None:
        suffix_stats: list[dict[str, float]] = [{} for _ in range(len(self._group_order) + 1)]
        suffix_sets: list[dict[str, int]] = [{} for _ in range(len(self._group_order) + 1)]
        suffix_melee = [0.0 for _ in range(len(self._group_order) + 1)]
        suffix_spell = [0.0 for _ in range(len(self._group_order) + 1)]
        self._group_stat_maxima = []
        self._group_set_caps = []
        self._all_stat_maxima = defaultdict(float)
        self._all_set_caps = defaultdict(int)
        self._all_melee_base = 0.0
        self._all_spell_base = 0.0

        for candidates in self._group_candidates:
            group_stat_max: dict[str, float] = {}
            for key in self._metric_keys_for_candidates:
                group_stat_max[key] = max((candidate.totals.get(key, 0.0) for candidate in candidates), default=0.0)
                self._all_stat_maxima[key] += group_stat_max[key]

            group_set_max: dict[str, int] = {}
            for candidate in candidates:
                for set_name, count in candidate.set_counts.items():
                    group_set_max[set_name] = max(group_set_max.get(set_name, 0), count)
            for set_name, count in group_set_max.items():
                self._all_set_caps[set_name] += count

            self._group_stat_maxima.append(group_stat_max)
            self._group_set_caps.append(group_set_max)
            self._all_melee_base = max(
                self._all_melee_base,
                max((candidate.totals.get(PSEUDO_MELEE_BASE, 0.0) for candidate in candidates), default=0.0),
            )
            self._all_spell_base = max(
                self._all_spell_base,
                max((candidate.totals.get(PSEUDO_SPELL_BASE, 0.0) for candidate in candidates), default=0.0),
            )

        for index in range(len(self._group_order) - 1, -1, -1):
            current_stats = dict(suffix_stats[index + 1])
            current_sets = dict(suffix_sets[index + 1])
            melee_base = suffix_melee[index + 1]
            spell_base = suffix_spell[index + 1]

            for key in self._metric_keys_for_candidates:
                current_stats[key] = current_stats.get(key, 0.0) + max(
                    (candidate.totals.get(key, 0.0) for candidate in self._group_candidates[index]),
                    default=0.0,
                )

            group_set_max: dict[str, int] = {}
            for candidate in self._group_candidates[index]:
                for set_name, count in candidate.set_counts.items():
                    group_set_max[set_name] = max(group_set_max.get(set_name, 0), count)
            for set_name, count in group_set_max.items():
                current_sets[set_name] = current_sets.get(set_name, 0) + count

            melee_base = max(
                melee_base,
                max((candidate.totals.get(PSEUDO_MELEE_BASE, 0.0) for candidate in self._group_candidates[index]), default=0.0),
            )
            spell_base = max(
                spell_base,
                max((candidate.totals.get(PSEUDO_SPELL_BASE, 0.0) for candidate in self._group_candidates[index]), default=0.0),
            )

            suffix_stats[index] = current_stats
            suffix_sets[index] = current_sets
            suffix_melee[index] = melee_base
            suffix_spell[index] = spell_base

        self._remaining_stat_maxima = suffix_stats
        self._remaining_set_piece_caps = suffix_sets
        self._remaining_melee_base = suffix_melee
        self._remaining_spell_base = suffix_spell

    def _apply_candidate(self, state: SearchState, candidate: GroupCandidate) -> SearchState:
        new_selections = dict(state.selections)
        new_selections.update({k: v for k, v in candidate.selections.items() if not k.startswith("__")})
        new_item_labels = tuple(sorted(state.item_labels + candidate.item_labels))

        new_totals = dict(state.item_totals)
        for key, value in candidate.totals.items():
            new_totals[key] = new_totals.get(key, 0.0) + value

        new_set_counts = dict(state.set_counts)
        for set_name, count in candidate.set_counts.items():
            new_set_counts[set_name] = new_set_counts.get(set_name, 0) + count

        return SearchState(
            group_index=state.group_index + 1,
            selections=new_selections,
            item_labels=new_item_labels,
            item_totals=new_totals,
            set_counts=new_set_counts,
            weapon_label=candidate.weapon_label or state.weapon_label,
            req_minima=self._requirement_minima_for_labels(new_item_labels),
        )

    def _constraints_still_possible(self, state: SearchState) -> bool:
        for constraint in self._constraints:
            if not self._constraint_possible_from_upper_bound(
                self._upper_bound_metric_for_state(state, constraint.metric_key),
                constraint,
            ):
                return False
        return True

    @staticmethod
    def _constraint_possible_from_upper_bound(upper_bound: float, constraint: OptimizationConstraint) -> bool:
        if constraint.operator == ">":
            return upper_bound > constraint.target
        if constraint.operator == "=":
            return upper_bound >= constraint.target or math.isclose(upper_bound, constraint.target, rel_tol=1e-9, abs_tol=1e-6)
        if constraint.operator == "<":
            return True
        raise ValueError(f"Unsupported constraint operator: {constraint.operator}")

    def _upper_bound_for_state(self, state: SearchState) -> float:
        if self._objective.is_single_metric():
            return self._upper_bound_metric_for_state(state, self._objective.primary_metric_key())
        return self._objective_upper_bound_from_state(state)

    def _objective_upper_bound_from_state(self, state: SearchState) -> float:
        total = 0.0
        for index, term in enumerate(self._objective.terms):
            upper_value = self._upper_bound_metric_for_state(state, term.metric_key)
            scale = self._objective.scale_for_index(index, upper_value)
            total += self._objective.normalized_weight(index) * (upper_value / scale)
        return total

    def _candidate_objective_upper_bound(
        self,
        group_index: int,
        candidate: GroupCandidate,
        upper_totals: dict[str, float],
    ) -> float:
        if self._objective.is_single_metric():
            return self._candidate_metric_upper_bound(group_index, candidate, upper_totals, self._objective.primary_metric_key())
        total = 0.0
        for index, term in enumerate(self._objective.terms):
            upper_value = self._candidate_metric_upper_bound(group_index, candidate, upper_totals, term.metric_key)
            scale = self._objective.scale_for_index(index, upper_value)
            total += self._objective.normalized_weight(index) * (upper_value / scale)
        return total

    def _upper_bound_metric_for_state(self, state: SearchState, metric_key: str) -> float:
        upper_totals = dict(state.item_totals)
        for key, value in self._remaining_stat_maxima[state.group_index].items():
            upper_totals[key] = upper_totals.get(key, 0.0) + value

        set_bonus_bound = self._optimistic_set_bonus_totals(state.set_counts, state.group_index)
        for key, value in set_bonus_bound.items():
            upper_totals[key] = upper_totals.get(key, 0.0) + value

        if metric_key == "hp_total":
            return upper_totals.get("hp", 0.0) + upper_totals.get("hpBonus", 0.0)
        if metric_key == "effective_hp":
            return self._effective_hp_upper_bound(upper_totals, state.req_minima)
        if metric_key == "melee_avg":
            base_total = 0.0
            if state.weapon_label:
                base_total = self.engine.weapon_melee_base_average(self.engine.item_lookup[state.weapon_label])
            else:
                base_total = self._remaining_melee_base[state.group_index]
            return self._damage_metric_upper_bound(base_total, upper_totals, "melee", state.req_minima)
        if metric_key == "spell_avg":
            base_total = 0.0
            if state.weapon_label:
                base_total = float(self.engine.item_lookup[state.weapon_label].get("averageDps", 0.0) or 0.0)
            else:
                base_total = self._remaining_spell_base[state.group_index]
            return self._damage_metric_upper_bound(base_total, upper_totals, "spell", state.req_minima)
        if metric_key in SKILLS:
            allocation = self._optimistic_base_allocation(state.req_minima, metric_key)
            return upper_totals.get(metric_key, 0.0) + allocation[SKILLS.index(metric_key)]
        return upper_totals.get(metric_key, 0.0)

    def _optimistic_set_bonus_totals(self, current_counts: dict[str, int], group_index: int) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)
        suffix_caps = self._remaining_set_piece_caps[group_index]
        set_names = set(current_counts) | set(suffix_caps)
        for set_name in set_names:
            current = current_counts.get(set_name, 0)
            max_extra = suffix_caps.get(set_name, 0)
            if max_extra <= 0 and current <= 0:
                continue
            max_count = min(current + max_extra, len(self.engine.sets.get(set_name, {}).get("items", [])))
            for key, value in self.engine.set_bonus_for_count(set_name, max_count).items():
                totals[key] += value
        return dict(totals)

    def _damage_metric_upper_bound(
        self,
        base_total: float,
        totals: dict[str, float],
        attack_type: str,
        req_minima: tuple[tuple[int, int, int, int, int], ...],
    ) -> float:
        if base_total <= 0:
            return 0.0

        allocation = self._optimistic_base_allocation(req_minima, "melee_avg" if attack_type == "melee" else "spell_avg")
        effective_skills = {
            skill: int(allocation[index] + totals.get(skill, 0.0))
            for index, skill in enumerate(SKILLS)
        }
        crit_chance = self.engine._skill_effect_percentage("dex", effective_skills["dex"]) / 100.0
        best_noncrit = max(
            self.engine._damage_boost_percent(element, attack_type, totals, effective_skills, False)
            for element in ELEMENT_ORDER
        )
        best_crit = max(
            self.engine._damage_boost_percent(element, attack_type, totals, effective_skills, True)
            for element in ELEMENT_ORDER
        )
        raw_total = sum(
            max(0.0, self.engine._raw_damage_bonus(element, attack_type, totals))
            for element in ELEMENT_ORDER
        )
        noncrit_total = (base_total * max(0.0, 1.0 + (best_noncrit / 100.0))) + raw_total
        crit_total = (base_total * max(0.0, 1.0 + (best_crit / 100.0))) + raw_total
        return (noncrit_total * (1.0 - crit_chance)) + (crit_total * crit_chance)

    def _effective_hp_upper_bound(
        self,
        totals: dict[str, float],
        req_minima: tuple[tuple[int, int, int, int, int], ...],
    ) -> float:
        allocation = self._optimistic_base_allocation(req_minima, "effective_hp")
        effective_skills = {
            skill: int(allocation[index] + totals.get(skill, 0.0))
            for index, skill in enumerate(SKILLS)
        }
        return self.engine._effective_hp_value(totals, effective_skills)

    def _optimistic_base_allocation(
        self,
        req_minima: tuple[tuple[int, int, int, int, int], ...],
        metric_key: str,
    ) -> tuple[int, int, int, int, int]:
        if req_minima:
            base = min(
                req_minima,
                key=lambda values: (level_105_allocation_shortfall(values), sum(values), values),
            )
        else:
            base = (0, 0, 0, 0, 0)

        allocation = [
            max(0, min(LEVEL_105_MAX_BASE_SKILL, int(base[index])))
            for index in range(5)
        ]
        remaining = max(0, LEVEL_105_TOTAL_SKILL_POINTS - sum(allocation))
        priorities = {
            "melee_avg": ("str", "dex"),
            "spell_avg": ("str", "dex", "int"),
            "effective_hp": ("def", "agi"),
            "str": ("str",),
            "dex": ("dex",),
            "int": ("int",),
            "def": ("def",),
            "agi": ("agi",),
        }.get(metric_key, ())

        for skill_name in priorities:
            skill_index = SKILLS.index(skill_name)
            take = min(remaining, LEVEL_105_MAX_BASE_SKILL - allocation[skill_index])
            allocation[skill_index] += take
            remaining -= take
            if remaining <= 0:
                break
        if remaining > 0:
            for skill_index in range(5):
                take = min(remaining, LEVEL_105_MAX_BASE_SKILL - allocation[skill_index])
                allocation[skill_index] += take
                remaining -= take
                if remaining <= 0:
                    break
        return tuple(allocation)


def merge_search_solutions(solution_groups: list[list[SearchSolution]], top_n: int) -> list[SearchSolution]:
    best_by_signature: dict[tuple[str, ...], SearchSolution] = {}
    for solutions in solution_groups:
        for solution in solutions:
            signature = solution.selection_values
            existing = best_by_signature.get(signature)
            if existing is None or solution.score > existing.score:
                best_by_signature[signature] = solution
    return sorted(
        best_by_signature.values(),
        key=lambda solution: (-solution.score, solution.selection_values),
    )[:top_n]


def _persistent_mcts_worker(
    data_path: str,
    task_queue: Any,
    progress_queue: Any,
) -> None:
    random.seed(time.time_ns() ^ os.getpid())
    engine = WynnBuildEngine(Path(data_path))
    optimizer = BuildOptimizer(engine)
    prepared_spaces: dict[tuple[Any, ...], PreparedSearchSpace] = {}

    while True:
        task = task_queue.get()
        if not task:
            continue
        command = task[0]
        if command == "shutdown":
            break
        if command != "run":
            continue

        _command, search_id, worker_id, space_id, prepared_space_payload, objective_metric, constraints, top_n, stop_event = task
        if prepared_space_payload is not None:
            prepared_spaces[space_id] = prepared_space_payload
        prepared_space = prepared_spaces.get(space_id)
        if prepared_space is None:
            progress_queue.put(("error", search_id, worker_id, f"Missing prepared search space for worker {worker_id}."))
            continue

        last_iterations = 0
        last_valid_count = 0
        last_summaries: list[SearchSolution] = []

        def summary_progress_callback(
            summaries: list[SearchSolution],
            iterations: int,
            valid_count: int,
            elapsed: float,
            detail: str,
        ) -> None:
            nonlocal last_iterations, last_valid_count, last_summaries
            last_iterations = iterations
            last_valid_count = valid_count
            last_summaries = list(summaries)
            progress_queue.put(("progress", search_id, worker_id, last_summaries, iterations, valid_count, elapsed, detail))

        started = time.perf_counter()
        try:
            optimizer.generate_mcts(
                {},
                None,
                objective_metric,
                list(constraints),
                top_n,
                stop_event=stop_event,
                summary_progress_callback=summary_progress_callback,
                prepared_space=prepared_space,
            )
            elapsed = time.perf_counter() - started
            progress_queue.put(("final", search_id, worker_id, last_summaries, last_iterations, last_valid_count, elapsed))
        except Exception as exc:
            progress_queue.put(("error", search_id, worker_id, f"{exc.__class__.__name__}: {exc}"))


class PersistentParallelMCTSPool:
    def __init__(self, engine: WynnBuildEngine, optimizer: BuildOptimizer) -> None:
        self.engine = engine
        self.optimizer = optimizer
        self.ctx = mp.get_context("spawn")
        self.manager = self.ctx.Manager()
        self.progress_queue = self.ctx.Queue()
        self.task_queues: list[Any] = []
        self.processes: list[mp.Process] = []
        self.worker_known_spaces: list[set[tuple[Any, ...]]] = []
        self._closed = False

    def _ensure_workers(self, worker_count: int) -> None:
        while len(self.processes) < worker_count:
            task_queue = self.ctx.Queue()
            process = self.ctx.Process(
                target=_persistent_mcts_worker,
                args=(str(self.engine.data_path), task_queue, self.progress_queue),
                daemon=True,
            )
            process.start()
            self.task_queues.append(task_queue)
            self.processes.append(process)
            self.worker_known_spaces.append(set())

    def run_search(
        self,
        prepared_space: PreparedSearchSpace,
        objective_metric: OptimizationObjective,
        constraints: list[OptimizationConstraint],
        top_n: int,
        worker_count: int,
        stop_event: threading.Event | None = None,
        progress_callback: Callable[[list[BuildOption], int, int, float, str], None] | None = None,
    ) -> list[BuildOption]:
        self.optimizer._activate_prepared_space(prepared_space, objective_metric, constraints)
        objective_spec = self.optimizer._objective
        if worker_count <= 1:
            return self.optimizer.generate_mcts(
                {},
                None,
                objective_spec,
                constraints,
                top_n,
                stop_event=stop_event,
                progress_callback=progress_callback,
                prepared_space=prepared_space,
            )

        self._ensure_workers(worker_count)
        while True:
            try:
                self.progress_queue.get_nowait()
            except queue.Empty:
                break

        process_stop_event = self.manager.Event()
        search_id = time.time_ns()
        started = time.perf_counter()
        next_emit = started
        constraints_tuple = tuple(constraints)
        worker_snapshots = {
            worker_id: {
                "solutions": [],
                "iterations": 0,
                "valid_count": 0,
            }
            for worker_id in range(worker_count)
        }
        finished_workers: set[int] = set()
        worker_error: str | None = None

        def emit_progress(force: bool = False) -> None:
            nonlocal next_emit
            if progress_callback is None:
                return
            now = time.perf_counter()
            if not force and now < next_emit:
                return
            merged_solutions = merge_search_solutions(
                [snapshot["solutions"] for snapshot in worker_snapshots.values()],
                top_n,
            )
            options = self.optimizer._materialize_solution_options(merged_solutions)
            total_iterations = sum(int(snapshot["iterations"]) for snapshot in worker_snapshots.values())
            total_valid = sum(int(snapshot["valid_count"]) for snapshot in worker_snapshots.values())
            active_workers = sum(1 for index in range(worker_count) if self.processes[index].is_alive())
            detail = f"{total_iterations} iterations across {worker_count} worker(s), {active_workers} active"
            progress_callback(
                options,
                total_iterations,
                total_valid,
                now - started,
                detail,
            )
            next_emit = now + 0.2

        try:
            for worker_id in range(worker_count):
                payload = None
                if prepared_space.cache_id not in self.worker_known_spaces[worker_id]:
                    payload = prepared_space
                    self.worker_known_spaces[worker_id].add(prepared_space.cache_id)
                self.task_queues[worker_id].put(
                    (
                        "run",
                        search_id,
                        worker_id,
                        prepared_space.cache_id,
                        payload,
                        objective_spec,
                        constraints_tuple,
                        top_n,
                        process_stop_event,
                    )
                )

            while True:
                if stop_event and stop_event.is_set():
                    process_stop_event.set()

                if worker_error is None and len(finished_workers) >= worker_count:
                    break

                try:
                    message = self.progress_queue.get(timeout=0.2)
                except queue.Empty:
                    message = None

                if message is None:
                    if all(not self.processes[index].is_alive() for index in range(worker_count)):
                        if len(finished_workers) < worker_count and worker_error is None:
                            worker_error = "One or more MCTS workers exited unexpectedly."
                        break
                    emit_progress()
                    continue

                status, message_search_id, worker_id, *payload = message
                if message_search_id != search_id or worker_id >= worker_count:
                    continue
                if status == "progress":
                    solutions, iterations, valid_count, _elapsed, _detail = payload
                    worker_snapshots[worker_id]["solutions"] = solutions
                    worker_snapshots[worker_id]["iterations"] = iterations
                    worker_snapshots[worker_id]["valid_count"] = valid_count
                    emit_progress()
                    continue
                if status == "final":
                    solutions, iterations, valid_count, _elapsed = payload
                    worker_snapshots[worker_id]["solutions"] = solutions
                    worker_snapshots[worker_id]["iterations"] = iterations
                    worker_snapshots[worker_id]["valid_count"] = valid_count
                    finished_workers.add(worker_id)
                    emit_progress(force=True)
                    continue
                if status == "error":
                    error_text = payload[0]
                    finished_workers.add(worker_id)
                    worker_error = error_text
                    process_stop_event.set()

            while True:
                try:
                    message = self.progress_queue.get_nowait()
                except queue.Empty:
                    break
                status, message_search_id, worker_id, *payload = message
                if message_search_id != search_id or worker_id >= worker_count:
                    continue
                if status == "progress":
                    solutions, iterations, valid_count, _elapsed, _detail = payload
                    worker_snapshots[worker_id]["solutions"] = solutions
                    worker_snapshots[worker_id]["iterations"] = iterations
                    worker_snapshots[worker_id]["valid_count"] = valid_count
                elif status == "final":
                    solutions, iterations, valid_count, _elapsed = payload
                    worker_snapshots[worker_id]["solutions"] = solutions
                    worker_snapshots[worker_id]["iterations"] = iterations
                    worker_snapshots[worker_id]["valid_count"] = valid_count
                    finished_workers.add(worker_id)
                elif status == "error":
                    worker_error = payload[0]

            if worker_error is not None:
                raise RuntimeError(worker_error)

            merged_solutions = merge_search_solutions(
                [snapshot["solutions"] for snapshot in worker_snapshots.values()],
                top_n,
            )
            return self.optimizer._materialize_solution_options(merged_solutions)
        finally:
            process_stop_event.set()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task_queue in self.task_queues:
            try:
                task_queue.put(("shutdown",))
            except Exception:
                pass
        for process in self.processes:
            process.join(timeout=1.0)
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        for process in self.processes:
            process.join(timeout=1.0)
        for task_queue in self.task_queues:
            task_queue.close()
            task_queue.join_thread()
        self.progress_queue.close()
        self.progress_queue.join_thread()
        self.manager.shutdown()
        self.task_queues = []
        self.processes = []
        self.worker_known_spaces = []


class SearchableCombobox(ttk.Frame):
    def __init__(self, master: tk.Misc, values: list[str], textvariable: tk.StringVar, **kwargs: Any) -> None:
        width = int(kwargs.pop("width", 20))
        super().__init__(master, **kwargs)
        self.all_values = list(dict.fromkeys(values))
        self.filtered_values = list(self.all_values)
        self.textvariable = textvariable
        self._popup: tk.Toplevel | None = None
        self._popup_frame: tk.Frame | None = None
        self._listbox: tk.Listbox | None = None
        self._scrollbar: ttk.Scrollbar | None = None
        self._close_job: str | None = None
        self._variable_trace = self.textvariable.trace_add("write", self._on_variable_changed)
        self._theme_colors_cache: dict[str, str] | None = None

        self.columnconfigure(0, weight=1)
        self.entry = ttk.Entry(self, textvariable=self.textvariable, width=width)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.button = ttk.Button(self, text="v", width=2, command=self._toggle_popup)
        self.button.grid(row=0, column=1, sticky="ns", padx=(4, 0))

        self.entry.bind("<KeyRelease>", self._on_key_release, add="+")
        self.entry.bind("<Down>", self._on_down_key, add="+")
        self.entry.bind("<Up>", self._on_up_key, add="+")
        self.entry.bind("<Return>", self._on_return_key, add="+")
        self.entry.bind("<Escape>", self._on_escape_key, add="+")
        self.entry.bind("<FocusOut>", self._schedule_popup_close, add="+")
        self.button.bind("<FocusOut>", self._schedule_popup_close, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")

    def get(self) -> str:
        return self.textvariable.get()

    def set_values(self, values: list[str]) -> None:
        self.all_values = list(dict.fromkeys(values))
        self._refresh_filtered_values()
        self._update_popup_contents()

    def apply_theme(self, colors: dict[str, str]) -> None:
        self._theme_colors_cache = dict(colors)
        if self._popup_frame is not None and self._popup_frame.winfo_exists():
            self._popup_frame.configure(bg=colors["border"], highlightbackground=colors["border"])
        if self._listbox is not None and self._listbox.winfo_exists():
            self._listbox.configure(
                bg=colors["input_bg"],
                fg=colors["fg"],
                selectbackground=colors["selection"],
                selectforeground=colors["selection_fg"],
                highlightbackground=colors["border"],
                highlightcolor=colors["accent"],
            )

    def _on_destroy(self, _event: tk.Event) -> None:
        if self.textvariable and self._variable_trace:
            try:
                self.textvariable.trace_remove("write", self._variable_trace)
            except tk.TclError:
                pass
            self._variable_trace = ""
        self._hide_popup()

    def _on_variable_changed(self, *_args: Any) -> None:
        self._refresh_filtered_values()
        self._update_popup_contents()

    def _refresh_filtered_values(self) -> None:
        query = self.get().strip().lower()
        if not query:
            self.filtered_values = list(self.all_values[:500])
            return
        self.filtered_values = [
            value
            for value in self.all_values
            if query in value.lower()
        ][:500]

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in {"Up", "Down", "Left", "Right", "Escape", "Return", "Tab"}:
            return
        self._refresh_filtered_values()
        if self.filtered_values:
            self._show_popup()
        else:
            self._hide_popup()

    def _on_down_key(self, _event: tk.Event) -> str:
        self._refresh_filtered_values()
        if not self.filtered_values:
            return "break"
        self._show_popup()
        self._move_listbox_selection(1)
        return "break"

    def _on_up_key(self, _event: tk.Event) -> str:
        if self._popup is None or self._listbox is None or not self._popup.winfo_exists():
            return "break"
        self._move_listbox_selection(-1)
        return "break"

    def _on_return_key(self, _event: tk.Event) -> str:
        self._refresh_filtered_values()
        if self._popup is not None and self._listbox is not None and self._popup.winfo_exists():
            self._select_listbox_value()
            return "break"
        if self.filtered_values:
            self._apply_selection(self.filtered_values[0])
            return "break"
        return "break"

    def _on_escape_key(self, _event: tk.Event) -> str:
        self._hide_popup()
        return "break"

    def _toggle_popup(self) -> None:
        self._refresh_filtered_values()
        if self._popup is not None and self._popup.winfo_exists():
            self._hide_popup()
            return
        self._show_popup()

    def _ensure_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            return
        self._popup = tk.Toplevel(self)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.transient(self.winfo_toplevel())
        self._popup_frame = tk.Frame(self._popup, bd=1, highlightthickness=1)
        self._popup_frame.pack(fill=tk.BOTH, expand=True)
        self._listbox = tk.Listbox(
            self._popup_frame,
            activestyle="none",
            exportselection=False,
            relief=tk.FLAT,
            highlightthickness=0,
        )
        self._scrollbar = ttk.Scrollbar(self._popup_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=self._scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.bind("<ButtonRelease-1>", self._on_listbox_click, add="+")
        self._listbox.bind("<Return>", self._on_listbox_return, add="+")
        self._listbox.bind("<Escape>", self._on_listbox_escape, add="+")
        self._listbox.bind("<FocusOut>", self._schedule_popup_close, add="+")
        if self._theme_colors_cache is not None:
            self.apply_theme(self._theme_colors_cache)

    def _show_popup(self) -> None:
        self._refresh_filtered_values()
        if not self.filtered_values:
            self._hide_popup()
            return
        self._ensure_popup()
        if self._popup is None or self._listbox is None:
            return
        self._update_popup_contents()
        width = max(self.winfo_width(), 180)
        visible_rows = min(max(1, len(self.filtered_values)), 12)
        height = max(140, visible_rows * 22)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self._popup.geometry(f"{width}x{height}+{x}+{y}")
        self._popup.deiconify()
        self._popup.lift()

    def _hide_popup(self) -> None:
        if self._close_job is not None:
            try:
                self.after_cancel(self._close_job)
            except tk.TclError:
                pass
            self._close_job = None
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.withdraw()

    def _update_popup_contents(self) -> None:
        if self._listbox is None or not self._listbox.winfo_exists():
            return
        current_selection = self.get().strip().lower()
        self._listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self._listbox.insert(tk.END, value)
        if not self.filtered_values:
            self._hide_popup()
            return
        preferred_index = 0
        for index, value in enumerate(self.filtered_values):
            if value.lower() == current_selection:
                preferred_index = index
                break
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(preferred_index)
        self._listbox.activate(preferred_index)
        self._listbox.see(preferred_index)

    def _move_listbox_selection(self, delta: int) -> None:
        if self._listbox is None or not self._listbox.winfo_exists() or not self.filtered_values:
            return
        selection = self._listbox.curselection()
        current_index = selection[0] if selection else 0
        next_index = max(0, min(len(self.filtered_values) - 1, current_index + delta))
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(next_index)
        self._listbox.activate(next_index)
        self._listbox.see(next_index)

    def _select_listbox_value(self) -> None:
        if self._listbox is None or not self._listbox.winfo_exists():
            return
        selection = self._listbox.curselection()
        if not selection:
            if self.filtered_values:
                self._apply_selection(self.filtered_values[0])
            return
        index = selection[0]
        if 0 <= index < len(self.filtered_values):
            self._apply_selection(self.filtered_values[index])

    def _apply_selection(self, value: str) -> None:
        self.textvariable.set(value)
        self.entry.icursor(tk.END)
        self.entry.focus_set()
        self._hide_popup()
        self.event_generate("<<SearchableComboboxSelected>>")

    def _on_listbox_click(self, _event: tk.Event) -> None:
        self._select_listbox_value()

    def _on_listbox_return(self, _event: tk.Event) -> str:
        self._select_listbox_value()
        return "break"

    def _on_listbox_escape(self, _event: tk.Event) -> str:
        self._hide_popup()
        self.entry.focus_set()
        return "break"

    def _schedule_popup_close(self, _event: tk.Event | None = None) -> None:
        if self._close_job is not None:
            try:
                self.after_cancel(self._close_job)
            except tk.TclError:
                pass
        self._close_job = self.after(120, self._close_popup_if_needed)

    def _close_popup_if_needed(self) -> None:
        self._close_job = None
        focus_widget = self.focus_get()
        if focus_widget is None:
            self._hide_popup()
            return
        current: tk.Misc | None = focus_widget
        while current is not None:
            if current in {self, self.entry, self.button, self._popup, self._popup_frame, self._listbox, self._scrollbar}:
                return
            current = getattr(current, "master", None)
        self._hide_popup()


class WynnBuildTesterApp(tk.Tk):
    def __init__(self, engine: WynnBuildEngine) -> None:
        super().__init__()
        self.engine = engine
        self.optimizer = BuildOptimizer(engine)
        self.parallel_mcts_pool = PersistentParallelMCTSPool(engine, self.optimizer)
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1200, 760)
        self._refresh_job: str | None = None
        self.optimizer_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.optimizer_thread: threading.Thread | None = None
        self.generated_options: list[BuildOption] = []
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.searchable_inputs: list[SearchableCombobox] = []
        self.slot_vars: dict[str, tk.StringVar] = {}
        self.slot_boxes: dict[str, SearchableCombobox] = {}
        self.default_combat_level = max(1, int(engine.max_item_level or DEFAULT_COMBAT_LEVEL_FALLBACK))
        self._active_combat_level_filter = self.default_combat_level
        self.combat_level_var = tk.StringVar(value=str(self.default_combat_level))
        self.damage_view_var = tk.StringVar(value="Melee")
        self.search_mode_var = tk.StringVar(value=SEARCH_MODE_LABELS[0])
        self.mcts_workers_var = tk.StringVar(value=str(default_mcts_worker_count(DETECTED_LOGICAL_CPUS)))
        self.top_n_var = tk.StringVar(value="5")
        self.dark_mode_var = tk.BooleanVar(value=True)
        self.exact_estimate_var = tk.StringVar(value="Exact estimate: click Estimate Exact Time for the current setup.")
        self.generator_status_var = tk.StringVar(
            value=self._default_generator_status()
        )
        self.objective_rows: list[dict[str, Any]] = []
        self.constraint_rows: list[dict[str, Any]] = []
        self.search_stop_event = threading.Event()

        self._build_layout()
        self.add_objective_row("HP", "1")
        self.add_constraint_row()
        self._update_search_mode_controls()
        self._apply_theme()

        for variable in self.slot_vars.values():
            variable.trace_add("write", self._schedule_refresh)
            variable.trace_add("write", self._invalidate_exact_estimate)
        self.damage_view_var.trace_add("write", self._schedule_refresh)
        self.search_mode_var.trace_add("write", self._update_search_mode_controls)
        self.search_mode_var.trace_add("write", self._invalidate_exact_estimate)
        self.mcts_workers_var.trace_add("write", self._invalidate_exact_estimate)
        self.top_n_var.trace_add("write", self._invalidate_exact_estimate)
        self.combat_level_var.trace_add("write", self._on_combat_level_changed)
        self.dark_mode_var.trace_add("write", self._apply_theme)

        self.protocol("WM_DELETE_WINDOW", self._handle_close)
        self.after_idle(self.refresh_results)

    def destroy(self) -> None:
        self.parallel_mcts_pool.close()
        super().destroy()

    @staticmethod
    def _default_generator_status() -> str:
        return (
            "Current gear entries are treated as required, and only items at or below the combat-level filter are considered. "
            "Base skills are auto-allocated per build for the selected "
            f"objective. Exact is optimal but slower; MCTS uses parallel processes and defaults to "
            f"{default_mcts_worker_count(DETECTED_LOGICAL_CPUS)} worker(s) on this device."
        )

    @staticmethod
    def _validate_integer_input(proposed: str) -> bool:
        return proposed == "" or proposed.isdigit()

    def _combat_level_filter(self, strict: bool = False) -> int | None:
        text = self.combat_level_var.get().strip()
        if not text:
            if strict:
                self.generator_status_var.set("Combat level is required before searching.")
            return None
        try:
            level = int(text)
        except ValueError:
            if strict:
                self.generator_status_var.set("Combat level must be a whole number.")
            return None
        if level < 1:
            if strict:
                self.generator_status_var.set("Combat level must be at least 1.")
            return None
        return level

    def _refresh_slot_level_filters(self) -> None:
        for slot_label, combo in self.slot_boxes.items():
            allowed_values = self.engine.slot_options_for_level(slot_label, self._active_combat_level_filter)
            combo.set_values(allowed_values)
            current = self.slot_vars[slot_label].get().strip()
            if current and current not in allowed_values:
                self.slot_vars[slot_label].set("")

    def _on_combat_level_changed(self, *_args: Any) -> None:
        level = self._combat_level_filter(strict=False)
        if level is None:
            self._invalidate_exact_estimate()
            self._schedule_refresh()
            return
        self._active_combat_level_filter = level
        self._refresh_slot_level_filters()
        self._invalidate_exact_estimate()
        self._schedule_refresh()

    def _theme_colors(self) -> dict[str, str]:
        return DARK_THEME if self.dark_mode_var.get() else LIGHT_THEME

    def _register_searchable(self, widget: SearchableCombobox) -> SearchableCombobox:
        self.searchable_inputs.append(widget)
        return widget

    def _style_text_widget(self, widget: tk.Text) -> None:
        colors = self._theme_colors()
        widget.configure(
            bg=colors["input_bg"],
            fg=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["selection"],
            selectforeground=colors["selection_fg"],
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
        )

    def _apply_theme(self, *_args: Any) -> None:
        colors = self._theme_colors()
        self.configure(bg=colors["bg"])

        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], padding=(0, 2))
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure(
            "TLabelframe",
            background=colors["bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            relief=tk.GROOVE,
        )
        self.style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])
        self.style.configure(
            "TButton",
            background=colors["button_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            padding=(8, 4),
        )
        self.style.map(
            "TButton",
            background=[("active", colors["button_active"]), ("pressed", colors["button_active"])],
            foreground=[("disabled", colors["muted"])],
        )
        self.style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        self.style.map(
            "TCheckbutton",
            background=[("active", colors["bg"])],
            foreground=[("disabled", colors["muted"])],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=colors["input_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            insertcolor=colors["fg"],
        )
        self.style.configure(
            "TSpinbox",
            fieldbackground=colors["input_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            insertcolor=colors["fg"],
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=colors["input_bg"],
            background=colors["input_bg"],
            foreground=colors["fg"],
            arrowcolor=colors["fg"],
            bordercolor=colors["border"],
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input_bg"])],
            selectbackground=[("readonly", colors["input_bg"])],
            selectforeground=[("readonly", colors["fg"])],
            foreground=[("readonly", colors["fg"])],
            background=[("readonly", colors["input_bg"])],
        )
        self.style.configure("TPanedwindow", background=colors["bg"])
        self.style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background=colors["button_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            padding=(12, 6),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", colors["input_bg"]), ("active", colors["button_active"])],
            foreground=[("selected", colors["fg"])],
        )
        self.style.configure(
            "Treeview",
            background=colors["input_bg"],
            fieldbackground=colors["input_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            rowheight=24,
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["selection"])],
            foreground=[("selected", colors["selection_fg"])],
        )
        self.style.configure(
            "Treeview.Heading",
            background=colors["button_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
        )

        self.option_add("*TCombobox*Listbox.background", colors["input_bg"])
        self.option_add("*TCombobox*Listbox.foreground", colors["fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", colors["selection"])
        self.option_add("*TCombobox*Listbox.selectForeground", colors["selection_fg"])

        self.searchable_inputs = [
            widget for widget in self.searchable_inputs
            if widget.winfo_exists()
        ]
        for widget in self.searchable_inputs:
            widget.apply_theme(colors)

        for widget in (self.summary_text, self.generated_details):
            self._style_text_widget(widget)

    def _update_search_mode_controls(self, *_args: Any) -> None:
        state = tk.NORMAL if SEARCH_MODE_OPTIONS.get(self.search_mode_var.get()) == "mcts" else tk.DISABLED
        self.mcts_workers_spinbox.configure(state=state)

    def _invalidate_exact_estimate(self, *_args: Any) -> None:
        self.exact_estimate_var.set("Exact estimate: click Estimate Exact Time for the current setup.")

    def _format_exact_estimate(
        self,
        estimate: ExactSearchEstimate,
        objective: OptimizationObjective,
        constraint_count: int,
    ) -> str:
        objective_label = objective.short_description()
        if estimate.completed_during_sample:
            return (
                f"Exact estimate: about {format_duration(estimate.estimated_seconds)} on this hardware. "
                f"The benchmark fully finished the current {objective_label} search with {constraint_count} constraint(s)."
            )
        if estimate.estimated_seconds >= 86400.0 * 365.0 * 100.0:
            return (
                "Exact estimate: well beyond practical exact-search time on this hardware "
                "(well over 100 years). "
                f"Sampled {format_number(estimate.sampled_states)} states at {format_number(estimate.states_per_second)} states/s "
                f"for {objective_label} with {constraint_count} constraint(s)."
            )
        if estimate.estimated_seconds >= 86400.0 * 30.0:
            return (
                f"Exact estimate: likely impractical on this hardware, around {format_duration(estimate.estimated_seconds)} "
                f"(rough range {format_duration(estimate.low_seconds)} to {format_duration(estimate.high_seconds)}). "
                f"Sampled {format_number(estimate.sampled_states)} states at {format_number(estimate.states_per_second)} states/s "
                f"for {objective_label} with {constraint_count} constraint(s)."
            )
        return (
            f"Exact estimate: about {format_duration(estimate.estimated_seconds)} on this hardware "
            f"(rough range {format_duration(estimate.low_seconds)} to {format_duration(estimate.high_seconds)}). "
            f"Sampled {format_number(estimate.sampled_states)} states at {format_number(estimate.states_per_second)} states/s "
            f"for {objective_label} with {constraint_count} constraint(s)."
        )

    def _handle_close(self) -> None:
        self.stop_generation()
        self.destroy()

    def _build_layout(self) -> None:
        container = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left = ttk.Frame(container, padding=12)
        right = ttk.Frame(container, padding=12)
        container.add(left, weight=1)
        container.add(right, weight=2)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        equipment_frame = ttk.LabelFrame(parent, text="Equipment", padding=12)
        equipment_frame.pack(fill=tk.X)

        level_validator = (self.register(self._validate_integer_input), "%P")
        ttk.Label(equipment_frame, text="Combat Level").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
        ttk.Spinbox(
            equipment_frame,
            from_=1,
            to=max(MAX_COMBAT_LEVEL_INPUT, self.engine.max_item_level, self.default_combat_level),
            textvariable=self.combat_level_var,
            width=8,
            validate="key",
            validatecommand=level_validator,
        ).grid(row=0, column=1, sticky="w", pady=4)

        for row, (slot_label, _slot_type) in enumerate(SLOT_CONFIGS, start=1):
            ttk.Label(equipment_frame, text=slot_label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 10))
            variable = tk.StringVar()
            combo = self._register_searchable(SearchableCombobox(
                equipment_frame,
                values=self.engine.slot_options_for_level(slot_label, self._active_combat_level_filter),
                textvariable=variable,
                width=42,
            ))
            combo.grid(row=row, column=1, sticky="ew", pady=4)
            self.slot_vars[slot_label] = variable
            self.slot_boxes[slot_label] = combo

        equipment_frame.columnconfigure(1, weight=1)

        buttons = ttk.Frame(parent)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Clear Gear", command=self.clear_gear).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Checkbutton(buttons, text="Dark Mode", variable=self.dark_mode_var).pack(side=tk.RIGHT)

        generator_frame = ttk.LabelFrame(parent, text="Generator", padding=12)
        generator_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        ttk.Label(generator_frame, text="Optimize For").grid(row=0, column=0, sticky="nw", pady=4, padx=(0, 8))
        objectives_frame = ttk.Frame(generator_frame)
        objectives_frame.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(objectives_frame, text="Metric").grid(row=0, column=0, sticky="w")
        ttk.Label(objectives_frame, text="Weight").grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.objectives_container = ttk.Frame(objectives_frame)
        self.objectives_container.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Button(objectives_frame, text="Add Objective", command=self.add_objective_row).grid(row=2, column=0, sticky="w", pady=(6, 0))
        objectives_frame.columnconfigure(0, weight=1)

        ttk.Label(generator_frame, text="Search Mode").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self.search_mode_box = ttk.Combobox(
            generator_frame,
            textvariable=self.search_mode_var,
            state="readonly",
            values=SEARCH_MODE_LABELS,
            width=28,
        )
        self.search_mode_box.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(generator_frame, text="MCTS Workers").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        workers_frame = ttk.Frame(generator_frame)
        workers_frame.grid(row=2, column=1, sticky="ew", pady=4)
        self.mcts_workers_spinbox = ttk.Spinbox(
            workers_frame,
            from_=1,
            to=DETECTED_LOGICAL_CPUS,
            textvariable=self.mcts_workers_var,
            width=8,
        )
        self.mcts_workers_spinbox.pack(side=tk.LEFT)
        ttk.Label(
            workers_frame,
            text=f"Detected {DETECTED_LOGICAL_CPUS} logical CPU(s); default {DEFAULT_MCTS_WORKERS}",
            wraplength=220,
            justify=tk.LEFT,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(generator_frame, text="Top Results").grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        ttk.Entry(generator_frame, textvariable=self.top_n_var, width=8).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(
            generator_frame,
            textvariable=self.exact_estimate_var,
            wraplength=360,
            justify=tk.LEFT,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 4))

        constraints_frame = ttk.Frame(generator_frame)
        constraints_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(4, 4))
        ttk.Label(constraints_frame, text="Constraints").grid(row=0, column=0, sticky="w")
        self.constraints_container = ttk.Frame(constraints_frame)
        self.constraints_container.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        generator_buttons = ttk.Frame(generator_frame)
        generator_buttons.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(generator_buttons, text="Add Constraint", command=self.add_constraint_row).pack(side=tk.LEFT)
        self.estimate_button = ttk.Button(generator_buttons, text="Estimate Exact Time", command=self.start_exact_estimate)
        self.estimate_button.pack(side=tk.LEFT, padx=(8, 0))
        self.generate_button = ttk.Button(generator_buttons, text="Generate Options", command=self.start_generation)
        self.generate_button.pack(side=tk.LEFT, padx=(8, 0))
        self.stop_generation_button = ttk.Button(generator_buttons, text="Stop Search", command=self.stop_generation, state=tk.DISABLED)
        self.stop_generation_button.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(
            generator_frame,
            textvariable=self.generator_status_var,
            wraplength=360,
            justify=tk.LEFT,
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

        generator_frame.columnconfigure(1, weight=1)

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        summary_tab = ttk.Frame(notebook, padding=12)
        damage_tab = ttk.Frame(notebook, padding=12)
        stats_tab = ttk.Frame(notebook, padding=12)
        generator_tab = ttk.Frame(notebook, padding=12)

        notebook.add(summary_tab, text="Summary")
        notebook.add(damage_tab, text="Damage")
        notebook.add(stats_tab, text="All Stats")
        notebook.add(generator_tab, text="Generator")

        self.summary_text = tk.Text(summary_tab, wrap=tk.WORD, height=24, state=tk.DISABLED)
        self.summary_text.pack(fill=tk.BOTH, expand=True)

        damage_header = ttk.Frame(damage_tab)
        damage_header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(damage_header, text="View").pack(side=tk.LEFT)
        self.damage_view_box = ttk.Combobox(
            damage_header,
            textvariable=self.damage_view_var,
            state="readonly",
            width=34,
            values=("Melee",),
        )
        self.damage_view_box.pack(side=tk.LEFT, padx=(8, 0))

        self.damage_summary_var = tk.StringVar(value="Pick a weapon to calculate damage.")
        ttk.Label(damage_tab, textvariable=self.damage_summary_var, wraplength=800, justify=tk.LEFT).pack(fill=tk.X)

        self.damage_tree = ttk.Treeview(
            damage_tab,
            columns=("part", "noncrit", "crit"),
            show="headings",
            height=9,
        )
        self.damage_tree.heading("part", text="Damage Part")
        self.damage_tree.heading("noncrit", text="Non-Crit")
        self.damage_tree.heading("crit", text="Crit")
        self.damage_tree.column("part", width=160, anchor=tk.W)
        self.damage_tree.column("noncrit", width=220, anchor=tk.W)
        self.damage_tree.column("crit", width=220, anchor=tk.W)
        self.damage_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        stats_header = ttk.Frame(stats_tab)
        stats_header.pack(fill=tk.X)
        ttk.Label(stats_header, text="Totals below include active set bonuses.").pack(side=tk.LEFT)

        self.stats_tree = ttk.Treeview(
            stats_tab,
            columns=("stat", "value"),
            show="headings",
        )
        self.stats_tree.heading("stat", text="Stat")
        self.stats_tree.heading("value", text="Total")
        self.stats_tree.column("stat", width=260, anchor=tk.W)
        self.stats_tree.column("value", width=180, anchor=tk.E)
        self.stats_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        generator_header = ttk.Frame(generator_tab)
        generator_header.pack(fill=tk.X)
        ttk.Label(generator_header, text="Top generated builds").pack(side=tk.LEFT)
        ttk.Button(generator_header, text="Apply Selected Option", command=self.apply_selected_generated_option).pack(side=tk.RIGHT)

        self.generated_tree = ttk.Treeview(
            generator_tab,
            columns=("rank", "score", "summary"),
            show="headings",
            height=8,
        )
        self.generated_tree.heading("rank", text="#")
        self.generated_tree.heading("score", text="Objective")
        self.generated_tree.heading("summary", text="Build")
        self.generated_tree.column("rank", width=50, anchor=tk.CENTER)
        self.generated_tree.column("score", width=140, anchor=tk.E)
        self.generated_tree.column("summary", width=520, anchor=tk.W)
        self.generated_tree.pack(fill=tk.BOTH, expand=True, pady=(8, 8))
        self.generated_tree.bind("<<TreeviewSelect>>", self._update_generated_details, add="+")
        self.generated_tree.bind("<Double-1>", lambda _event: self.apply_selected_generated_option(), add="+")

        self.generated_details = tk.Text(generator_tab, wrap=tk.WORD, height=14, state=tk.DISABLED)
        self.generated_details.pack(fill=tk.BOTH, expand=True)

    def clear_gear(self) -> None:
        for variable in self.slot_vars.values():
            variable.set("")

    def clear_all(self) -> None:
        self.clear_gear()
        self.combat_level_var.set(str(self.default_combat_level))
        self.search_mode_var.set(SEARCH_MODE_LABELS[0])
        self.mcts_workers_var.set(str(default_mcts_worker_count(DETECTED_LOGICAL_CPUS)))
        self.top_n_var.set("5")
        for row in list(self.objective_rows):
            row["frame"].destroy()
        self.objective_rows.clear()
        self.add_objective_row("HP", "1")
        for row in list(self.constraint_rows):
            row["frame"].destroy()
        self.constraint_rows.clear()
        self.add_constraint_row()
        self.generated_options = []
        self._update_generated_tree([])
        self.exact_estimate_var.set("Exact estimate: click Estimate Exact Time for the current setup.")
        self.generator_status_var.set(self._default_generator_status())

    def add_objective_row(self, metric_label: str = "", weight_value: str = "1") -> None:
        row_index = len(self.objective_rows)
        frame = ttk.Frame(self.objectives_container)
        frame.grid(row=row_index, column=0, sticky="ew", pady=2)

        metric_var = tk.StringVar(value=metric_label)
        weight_var = tk.StringVar(value=weight_value)
        metric_var.trace_add("write", self._schedule_refresh)
        metric_var.trace_add("write", self._invalidate_exact_estimate)
        weight_var.trace_add("write", self._schedule_refresh)
        weight_var.trace_add("write", self._invalidate_exact_estimate)

        metric_box = self._register_searchable(SearchableCombobox(
            frame,
            values=METRIC_DISPLAY_OPTIONS,
            textvariable=metric_var,
            width=22,
        ))
        metric_box.grid(row=0, column=0, sticky="ew")
        ttk.Entry(frame, textvariable=weight_var, width=8).grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Button(frame, text="Remove", command=lambda: self.remove_objective_row(frame)).grid(row=0, column=2, padx=(6, 0))
        frame.columnconfigure(0, weight=1)

        self.objective_rows.append({
            "frame": frame,
            "metric_var": metric_var,
            "weight_var": weight_var,
            "metric_box": metric_box,
        })
        self._apply_theme()

    def remove_objective_row(self, frame: ttk.Frame) -> None:
        self.objective_rows = [row for row in self.objective_rows if row["frame"] is not frame]
        frame.destroy()
        if not self.objective_rows:
            self.add_objective_row("HP", "1")
            return
        for index, row in enumerate(self.objective_rows):
            row["frame"].grid_configure(row=index)
        self._invalidate_exact_estimate()
        self._schedule_refresh()

    def add_constraint_row(self, metric_label: str = "", operator: str = ">", target_value: str = "") -> None:
        row_index = len(self.constraint_rows)
        frame = ttk.Frame(self.constraints_container)
        frame.grid(row=row_index, column=0, sticky="ew", pady=2)

        metric_var = tk.StringVar(value=metric_label)
        operator_var = tk.StringVar(value=operator if operator in CONSTRAINT_OPERATORS else ">")
        target_var = tk.StringVar(value=target_value)
        metric_var.trace_add("write", self._invalidate_exact_estimate)
        operator_var.trace_add("write", self._invalidate_exact_estimate)
        target_var.trace_add("write", self._invalidate_exact_estimate)

        metric_box = self._register_searchable(SearchableCombobox(
            frame,
            values=METRIC_DISPLAY_OPTIONS,
            textvariable=metric_var,
            width=24,
        ))
        metric_box.grid(row=0, column=0, sticky="ew")
        operator_box = ttk.Combobox(
            frame,
            textvariable=operator_var,
            state="readonly",
            values=CONSTRAINT_OPERATORS,
            width=4,
        )
        operator_box.grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Entry(frame, textvariable=target_var, width=10).grid(row=0, column=2, sticky="w", padx=(6, 0))
        ttk.Button(frame, text="Remove", command=lambda: self.remove_constraint_row(frame)).grid(row=0, column=3, padx=(6, 0))
        frame.columnconfigure(0, weight=1)

        self.constraint_rows.append({
            "frame": frame,
            "metric_var": metric_var,
            "operator_var": operator_var,
            "target_var": target_var,
        })
        self._apply_theme()

    def remove_constraint_row(self, frame: ttk.Frame) -> None:
        self.constraint_rows = [row for row in self.constraint_rows if row["frame"] is not frame]
        frame.destroy()
        for index, row in enumerate(self.constraint_rows):
            row["frame"].grid_configure(row=index)
        self._invalidate_exact_estimate()

    def _collect_objective(
        self,
        strict: bool = True,
    ) -> OptimizationObjective | None:
        entries: list[tuple[str, float]] = []
        for row in self.objective_rows:
            metric_text = row["metric_var"].get().strip()
            weight_text = row["weight_var"].get().strip()
            if not metric_text and not weight_text:
                continue
            if not metric_text:
                if strict:
                    self.generator_status_var.set("Each objective row needs a metric.")
                    return None
                continue
            metric_key = resolve_metric_key(metric_text)
            if metric_key is None:
                if strict:
                    self.generator_status_var.set(f"Unknown objective metric: {metric_text}")
                    return None
                continue
            try:
                weight_value = float(weight_text or "1")
            except ValueError:
                if strict:
                    self.generator_status_var.set(f"Invalid objective weight: {weight_text}")
                    return None
                continue
            if weight_value <= 0.0:
                if strict:
                    self.generator_status_var.set("Objective weights must be greater than 0.")
                    return None
                continue
            entries.append((metric_key, weight_value))

        if not entries:
            return make_optimization_objective((("hp_total", 1.0),))
        return make_optimization_objective(entries)

    def _collect_generator_inputs(
        self,
        validate_mcts_workers: bool = True,
    ) -> tuple[OptimizationObjective, str, list[OptimizationConstraint], int, dict[str, str], int, int] | None:
        objective = self._collect_objective(strict=True)
        if objective is None:
            return None
        combat_level = self._combat_level_filter(strict=True)
        if combat_level is None:
            return None
        search_mode = SEARCH_MODE_OPTIONS.get(self.search_mode_var.get())
        if search_mode is None:
            self.generator_status_var.set("Choose a valid search mode.")
            return None

        constraints: list[OptimizationConstraint] = []
        for row in self.constraint_rows:
            metric_text = row["metric_var"].get().strip()
            operator_text = row["operator_var"].get().strip() or ">"
            target_text = row["target_var"].get().strip()
            if not metric_text and not target_text:
                continue
            metric_key = resolve_metric_key(metric_text)
            if metric_key is None:
                self.generator_status_var.set(f"Unknown constraint metric: {metric_text}")
                return None
            if operator_text not in CONSTRAINT_OPERATORS:
                self.generator_status_var.set(f"Unknown constraint operator: {operator_text}")
                return None
            try:
                target_value = float(target_text or "0")
            except ValueError:
                self.generator_status_var.set(f"Invalid constraint value: {target_text}")
                return None
            constraints.append(OptimizationConstraint(metric_key, operator_text, target_value))

        try:
            top_n = max(1, min(20, int(self.top_n_var.get().strip() or "5")))
        except ValueError:
            self.generator_status_var.set("Top results must be a whole number.")
            return None

        mcts_worker_count = default_mcts_worker_count(DETECTED_LOGICAL_CPUS)
        if validate_mcts_workers and search_mode == "mcts":
            worker_text = self.mcts_workers_var.get().strip() or str(mcts_worker_count)
            try:
                mcts_worker_count = int(worker_text)
            except ValueError:
                self.generator_status_var.set("MCTS workers must be a whole number.")
                return None
            if not 1 <= mcts_worker_count <= DETECTED_LOGICAL_CPUS:
                self.generator_status_var.set(
                    f"MCTS workers must be between 1 and {DETECTED_LOGICAL_CPUS} on this device."
                )
                return None

        required_selections = {
            slot: value.strip()
            for slot, value in self._current_selections().items()
            if value.strip()
        }
        for slot, value in required_selections.items():
            if value not in self.engine.slot_options_for_level(slot, combat_level):
                self.generator_status_var.set(
                    f"{slot} must be a recognized item at or below combat level {combat_level} before it can be required."
                )
                return None

        return objective, search_mode, constraints, top_n, required_selections, mcts_worker_count, combat_level

    def start_exact_estimate(self) -> None:
        if self.optimizer_thread and self.optimizer_thread.is_alive():
            return

        generator_inputs = self._collect_generator_inputs(validate_mcts_workers=False)
        if generator_inputs is None:
            return
        objective, _search_mode, constraints, top_n, required_selections, _mcts_worker_count, combat_level = generator_inputs

        while True:
            try:
                self.optimizer_queue.get_nowait()
            except queue.Empty:
                break

        self.generate_button.configure(state=tk.DISABLED)
        self.estimate_button.configure(state=tk.DISABLED)
        self.stop_generation_button.configure(state=tk.DISABLED)
        self.exact_estimate_var.set("Exact estimate: benchmarking current setup on this hardware...")
        self.generator_status_var.set("Benchmarking the current exact-search setup to estimate runtime...")

        def worker() -> None:
            try:
                estimate = self.optimizer.estimate_exact_search(
                    required_selections,
                    objective,
                    constraints,
                    top_n,
                    combat_level,
                )
                self.optimizer_queue.put(("estimate_result", estimate, objective, len(constraints)))
            except Exception as exc:
                self.optimizer_queue.put(("error", str(exc)))

        self.optimizer_thread = threading.Thread(target=worker, daemon=True)
        self.optimizer_thread.start()
        self.after(100, self._poll_optimizer_queue)

    def start_generation(self) -> None:
        if self.optimizer_thread and self.optimizer_thread.is_alive():
            return

        generator_inputs = self._collect_generator_inputs()
        if generator_inputs is None:
            return
        objective, search_mode, constraints, top_n, required_selections, mcts_worker_count, combat_level = generator_inputs

        while True:
            try:
                self.optimizer_queue.get_nowait()
            except queue.Empty:
                break

        self.search_stop_event.clear()
        self.generate_button.configure(state=tk.DISABLED)
        self.estimate_button.configure(state=tk.DISABLED)
        self.stop_generation_button.configure(state=tk.NORMAL)
        if search_mode == "mcts":
            self.generator_status_var.set(
                f"Running MCTS search with {mcts_worker_count} worker(s). Click Stop Search whenever you want to keep the current best builds."
            )
        else:
            self.generator_status_var.set("Running exact search for fully optimized builds...")
        self.generated_options = []
        self._update_generated_tree([])

        def progress_callback(options: list[BuildOption], iterations: int, valid_count: int, elapsed: float, detail: str) -> None:
            self.optimizer_queue.put(
                ("progress", options, objective, elapsed, detail, search_mode, iterations, valid_count, mcts_worker_count)
            )

        def worker() -> None:
            started = time.perf_counter()
            try:
                prepared_space = self.optimizer._prepare_search(
                    required_selections,
                    objective,
                    constraints,
                    combat_level,
                )
                if search_mode == "mcts":
                    options = self.parallel_mcts_pool.run_search(
                        prepared_space,
                        self.optimizer._objective,
                        constraints,
                        top_n,
                        mcts_worker_count,
                        stop_event=self.search_stop_event,
                        progress_callback=progress_callback,
                    )
                else:
                    options = self.optimizer.generate(
                        required_selections,
                        None,
                        objective,
                        constraints,
                        top_n,
                        combat_level,
                        stop_event=self.search_stop_event,
                        progress_callback=progress_callback,
                        prepared_space=prepared_space,
                    )
                elapsed = time.perf_counter() - started
                final_status = "stopped" if self.search_stop_event.is_set() else "success"
                self.optimizer_queue.put((final_status, options, objective, elapsed, search_mode, mcts_worker_count))
            except Exception as exc:
                self.optimizer_queue.put(("error", str(exc)))

        self.optimizer_thread = threading.Thread(target=worker, daemon=True)
        self.optimizer_thread.start()
        self.after(100, self._poll_optimizer_queue)

    def stop_generation(self) -> None:
        if not self.optimizer_thread or not self.optimizer_thread.is_alive():
            return
        self.search_stop_event.set()
        self.stop_generation_button.configure(state=tk.DISABLED)
        self.generator_status_var.set("Stopping search and keeping the best options found so far...")

    def _poll_optimizer_queue(self) -> None:
        received_message = False
        while True:
            try:
                message = self.optimizer_queue.get_nowait()
            except queue.Empty:
                break

            received_message = True
            status = message[0]
            if status == "progress":
                _status, options, objective, elapsed, detail, search_mode, iterations, valid_count, worker_count = message
                self.generated_options = options
                self._update_generated_tree(options)
                if search_mode == "mcts":
                    mode_label = f"MCTS ({worker_count} worker{'s' if worker_count != 1 else ''})"
                else:
                    mode_label = "Exact"
                self.generator_status_var.set(
                    f"{mode_label} search running: {detail}. Valid builds found so far: {valid_count}. Current top {len(options)} build(s) for {objective.short_description()} after {elapsed:.2f}s."
                )
                continue

            self.generate_button.configure(state=tk.NORMAL)
            self.estimate_button.configure(state=tk.NORMAL)
            self.stop_generation_button.configure(state=tk.DISABLED)
            if status == "estimate_result":
                _status, estimate, objective, constraint_count = message
                estimate_text = self._format_exact_estimate(estimate, objective, constraint_count)
                self.exact_estimate_var.set(estimate_text)
                self.generator_status_var.set(estimate_text)
                continue
            if status in {"success", "stopped"}:
                _status, options, objective, elapsed, search_mode, worker_count = message
                self.generated_options = options
                self._update_generated_tree(options)
                if status == "stopped":
                    if search_mode == "mcts":
                        self.generator_status_var.set(
                            f"Stopped MCTS search after {elapsed:.2f}s with {len(options)} build option(s) for {objective.short_description()} using {worker_count} worker(s)."
                        )
                    else:
                        self.generator_status_var.set(
                            f"Stopped exact search after {elapsed:.2f}s with {len(options)} build option(s) for {objective.short_description()}."
                        )
                else:
                    if search_mode == "mcts":
                        self.generator_status_var.set(
                            f"Found {len(options)} build option(s) for {objective.short_description()} in {elapsed:.2f}s using {worker_count} MCTS worker(s)."
                        )
                    else:
                        self.generator_status_var.set(
                            f"Found {len(options)} build option(s) for {objective.short_description()} in {elapsed:.2f}s."
                        )
            else:
                self.generator_status_var.set(f"Generator failed: {message[1]}")

        if self.optimizer_thread and self.optimizer_thread.is_alive():
            self.after(100, self._poll_optimizer_queue)
        elif not received_message:
            self.generate_button.configure(state=tk.NORMAL)
            self.estimate_button.configure(state=tk.NORMAL)
            self.stop_generation_button.configure(state=tk.DISABLED)

    def _update_generated_tree(self, options: list[BuildOption]) -> None:
        previous_selection = self.generated_tree.selection()
        for row_id in self.generated_tree.get_children():
            self.generated_tree.delete(row_id)

        for index, option in enumerate(options, start=1):
            summary = ", ".join(
                option.selections.get(slot, "-")
                for slot, _ in SLOT_CONFIGS
            )
            self.generated_tree.insert(
                "",
                tk.END,
                iid=str(index - 1),
                values=(index, format_number(option.objective_value), summary),
            )

        if previous_selection and previous_selection[0] in self.generated_tree.get_children():
            self.generated_tree.selection_set(previous_selection[0])
            self._update_generated_details()
        else:
            self._set_generated_details("Select a generated build to inspect it." if options else "No generated builds yet.")

    def _selected_generated_option(self) -> BuildOption | None:
        selection = self.generated_tree.selection()
        if not selection:
            return None
        try:
            index = int(selection[0])
        except ValueError:
            return None
        if 0 <= index < len(self.generated_options):
            return self.generated_options[index]
        return None

    def _update_generated_details(self, _event: tk.Event | None = None) -> None:
        option = self._selected_generated_option()
        if option is None:
            self._set_generated_details("Select a generated build to inspect it.")
            return

        result = option.result
        lines = [
            f"{option.objective_label}: {format_number(option.objective_value)}",
            f"HP: {format_number(self.engine.metric_value_from_result(result, 'hp_total'))}",
            f"Effective HP: {format_number(self.engine.metric_value_from_result(result, 'effective_hp'))}",
            f"Melee Avg Damage: {format_number(self.engine.metric_value_from_result(result, 'melee_avg'))}",
            f"Spell Avg Damage: {format_number(self.engine.metric_value_from_result(result, 'spell_avg'))}",
        ]
        if not option.objective.is_single_metric():
            lines.extend([
                "",
                "Objective Breakdown",
            ])
            for label, weight, raw_value, contribution in self.engine.objective_breakdown_from_result(result, option.objective):
                lines.append(
                    f"  {label} x{format_number(weight)}: {format_number(raw_value)} (score contribution {format_number(contribution)})"
                )
        lines.extend([
            "",
            f"Auto Allocation ({result.allocation_metric_label})",
        ])
        for skill in SKILLS:
            lines.append(f"  {SKILL_LABELS[skill]}: {result.base_skills[skill]}")

        lines.extend([
            "",
            "Gear",
        ])
        for slot_label, _slot_type in SLOT_CONFIGS:
            lines.append(f"  {slot_label}: {option.selections.get(slot_label, '-')}")

        if option.constraint_values:
            lines.append("")
            lines.append("Constraints")
            for label, value in option.constraint_values.items():
                lines.append(f"  {label}: {format_number(value)}")

        lines.append("")
        lines.append(f"Equip Order: {' -> '.join(result.equip_order or []) if result.equip_order else 'None'}")
        self._set_generated_details("\n".join(lines))

    def _set_generated_details(self, text: str) -> None:
        self.generated_details.configure(state=tk.NORMAL)
        self.generated_details.delete("1.0", tk.END)
        self.generated_details.insert("1.0", text)
        self.generated_details.configure(state=tk.DISABLED)

    def apply_selected_generated_option(self) -> None:
        option = self._selected_generated_option()
        if option is None:
            return
        for slot, variable in self.slot_vars.items():
            value = option.selections.get(slot, "")
            allowed_values = self.engine.slot_options_for_level(slot, self._active_combat_level_filter)
            variable.set(value if not value or value in allowed_values else "")

    def _schedule_refresh(self, *_args: Any) -> None:
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(120, self.refresh_results)

    def refresh_results(self) -> None:
        self._refresh_job = None
        objective = self._collect_objective(strict=False) or make_optimization_objective((("hp_total", 1.0),))
        result = self.engine.build_result(self._current_selections(), objective)
        self._update_summary(result)
        self._update_damage(result)
        self._update_stats(result)

    def _current_selections(self) -> dict[str, str]:
        return {slot: variable.get() for slot, variable in self.slot_vars.items()}

    def _update_summary(self, result: BuildResult) -> None:
        lines: list[str] = []

        if result.selected_items:
            lines.append("Selected Gear")
            for slot_label, _slot_type in SLOT_CONFIGS:
                item = result.selected_items.get(slot_label)
                if item:
                    lines.append(f"  {slot_label}: {item['_label']}")
        else:
            lines.append("Selected Gear")
            lines.append("  No items selected yet.")

        lines.append("")
        lines.append("Build Summary")
        lines.append(f"  Combat level filter: {self._active_combat_level_filter}")
        lines.append(f"  Level requirement: {result.level_requirement}")
        lines.append(f"  Weapon class: {result.weapon_class or 'None'}")
        lines.append(f"  Gear health bonus: {format_number(result.gear_health_bonus)}")
        lines.append(f"  Effective HP: {format_number(self.engine.metric_value_from_result(result, 'effective_hp'))}")

        lines.append("")
        lines.append("Auto-Allocated Skill Points")
        lines.append(
            f"  Optimized for: {result.allocation_metric_label}"
        )
        lines.append(
            f"  Base total: {result.base_skill_total} / {LEVEL_105_TOTAL_SKILL_POINTS} "
            f"(max {LEVEL_105_MAX_BASE_SKILL} in one stat)"
        )
        for skill in SKILLS:
            base_value = result.base_skills[skill]
            bonus_value = result.totals.get(skill, 0.0)
            total_value = result.effective_skills[skill]
            percentage = self.engine._skill_effect_percentage(skill, total_value)
            lines.append(
                f"  {SKILL_LABELS[skill]}: {base_value} base + {format_number(bonus_value)} gear = {total_value} total ({format_percent(percentage)})"
            )

        if result.weapon:
            atk_speed = str(result.weapon.get("atkSpd", "UNKNOWN")).replace("_", " ").title()
            average_dps = result.weapon.get("averageDps")
            if average_dps:
                lines.append("")
                lines.append(f"Weapon speed: {atk_speed}")
                lines.append(f"Weapon listed DPS: {format_number(float(average_dps))}")
            melee_avg = self.engine.metric_value_from_result(result, "melee_avg")
            spell_avg = self.engine.metric_value_from_result(result, "spell_avg")
            lines.append(f"Estimated melee average: {format_number(melee_avg)}")
            lines.append(f"Estimated spell average: {format_number(spell_avg)}")

        lines.append("")
        lines.append("Equip Order")
        if result.equip_order is None:
            lines.append("  No stable equip order found within the level 105 skill-point budget.")
        elif not result.equip_order:
            lines.append("  No gear selected.")
        else:
            order_text = " -> ".join(
                f"{slot} ({result.selected_items[slot]['_label']})"
                for slot in result.equip_order
            )
            lines.append(f"  {order_text}")

        if result.active_sets:
            lines.append("")
            lines.append("Active Sets")
            for set_name, piece_count, bonus in result.active_sets:
                bonus_text = self._format_bonus_dict(bonus) if bonus else "No stat bonus at this piece count."
                lines.append(f"  {set_name} x{piece_count}: {bonus_text}")

        if result.warnings:
            lines.append("")
            lines.append("Warnings")
            for warning in result.warnings:
                lines.append(f"  - {warning}")

        self.summary_text.configure(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", "\n".join(lines))
        self.summary_text.configure(state=tk.DISABLED)

    def _update_damage(self, result: BuildResult) -> None:
        available_profiles = list(result.damage_profiles.keys()) or ["Melee"]
        self.damage_view_box.configure(values=available_profiles)
        if self.damage_view_var.get() not in available_profiles:
            self.damage_view_var.set(available_profiles[0])

        for row_id in self.damage_tree.get_children():
            self.damage_tree.delete(row_id)

        profile = result.damage_profiles.get(self.damage_view_var.get())
        if profile is None:
            self.damage_summary_var.set("Pick a weapon to calculate damage.")
            return

        noncrit_total = total_damage_range(profile.noncrit)
        crit_total = total_damage_range(profile.crit)
        expected_total = DamageRange(
            minimum=(noncrit_total.minimum * (1.0 - profile.crit_chance)) + (crit_total.minimum * profile.crit_chance),
            maximum=(noncrit_total.maximum * (1.0 - profile.crit_chance)) + (crit_total.maximum * profile.crit_chance),
        )
        strength_poison = 0.0
        if result.totals.get("poison"):
            strength_bonus = self.engine._skill_effect_percentage("str", result.effective_skills["str"]) / 100.0
            strength_poison = math.ceil((result.totals.get("poison", 0.0) / 3.0) * (1.0 + strength_bonus))

        if profile.attack_type == "spell":
            summary = (
                f"Crit chance {format_percent(profile.crit_chance * 100.0)} | "
                f"Scaled from listed weapon DPS | "
                f"Expected total {format_damage_range(expected_total)}"
            )
        else:
            summary = (
                f"Crit chance {format_percent(profile.crit_chance * 100.0)} | "
                f"Weapon speed {profile.attack_speed_label} | "
                f"Expected total {format_damage_range(expected_total)}"
            )
        if strength_poison:
            summary += f" | Poison / tick {format_number(strength_poison)}"
        if profile.note:
            summary += f" | Note: {profile.note}"
        self.damage_summary_var.set(summary)

        for element in ELEMENT_ORDER:
            self.damage_tree.insert(
                "",
                tk.END,
                values=(
                    ELEMENT_LABELS[element],
                    format_damage_range(profile.noncrit[element]),
                    format_damage_range(profile.crit[element]),
                ),
            )
        self.damage_tree.insert(
            "",
            tk.END,
            values=(
                "Total",
                format_damage_range(noncrit_total),
                format_damage_range(crit_total),
            ),
        )

    def _update_stats(self, result: BuildResult) -> None:
        for row_id in self.stats_tree.get_children():
            self.stats_tree.delete(row_id)

        keys = [key for key in DISPLAY_STAT_ORDER if not math.isclose(result.totals.get(key, 0.0), 0.0, abs_tol=1e-9)]
        remaining = sorted(
            [
                key
                for key, value in result.totals.items()
                if key not in STRUCTURAL_KEYS and key not in DISPLAY_STAT_ORDER and is_number(value) and not math.isclose(value, 0.0, abs_tol=1e-9)
            ],
            key=str.casefold,
        )
        keys.extend(remaining)

        if not keys:
            self.stats_tree.insert("", tk.END, values=("No non-zero totals yet.", ""))
            return

        for key in keys:
            self.stats_tree.insert("", tk.END, values=(normalize_stat_key(key), format_number(result.totals[key])))

    @staticmethod
    def _format_bonus_dict(bonus: dict[str, float]) -> str:
        if not bonus:
            return "No bonus"
        parts = [
            f"{normalize_stat_key(key)} {format_number(value)}"
            for key, value in sorted(bonus.items())
            if is_number(value)
        ]
        return ", ".join(parts) if parts else "No numeric bonus"


def run_self_test(engine: WynnBuildEngine) -> int:
    if not math.isclose(engine._skill_effect_percentage("def", 150), 70.0, abs_tol=0.1):
        raise AssertionError("Defence scaling no longer matches the current skill-point curve.")
    if not math.isclose(engine._skill_effect_percentage("agi", 150), 76.8, abs_tol=0.1):
        raise AssertionError("Agility scaling no longer matches the current skill-point curve.")
    if not math.isclose(engine._intelligence_spell_cost_reduction_percentage(150), 50.0, abs_tol=0.05):
        raise AssertionError("Intelligence spell-cost reduction no longer matches the current skill-point curve.")

    sample_totals = {"hp": 1000.0}
    sample_skills = {"str": 0, "dex": 0, "int": 0, "def": 150, "agi": 150}
    expected_multiplier = (
        (engine._skill_effect_percentage("agi", sample_skills["agi"]) / 100.0) * 0.1
    ) + (
        (1.0 - (engine._skill_effect_percentage("agi", sample_skills["agi"]) / 100.0))
        * (1.0 - (engine._skill_effect_percentage("def", sample_skills["def"]) / 100.0))
    )
    expected_ehp = sample_totals["hp"] / expected_multiplier
    if not math.isclose(engine._effective_hp_value(sample_totals, sample_skills), expected_ehp, rel_tol=1e-9):
        raise AssertionError("Effective HP is no longer using the wiki dodge-plus-defence interaction.")

    thunder_crit_boost = engine._damage_boost_percent(
        "t",
        "melee",
        {},
        {"str": 0, "dex": 100, "int": 0, "def": 0, "agi": 0},
        True,
    )
    if not math.isclose(thunder_crit_boost, 230.0, abs_tol=0.1):
        raise AssertionError("Thunder critical scaling no longer matches the wiki dexterity interaction.")

    selections = {}
    for slot_label, _slot_type in SLOT_CONFIGS:
        options = engine.slot_options[slot_label]
        if options:
            selections[slot_label] = options[0]

    result = engine.build_result(selections, "hp_total")

    print("Loaded items:", len(engine.items))
    print("Selected weapon:", result.weapon["_label"] if result.weapon else "None")
    print("Level requirement:", result.level_requirement)
    print("Gear health bonus:", format_number(result.gear_health_bonus))
    print("Auto allocation:", ", ".join(f"{skill}={result.base_skills[skill]}" for skill in SKILLS))
    print("Equip order:", " -> ".join(result.equip_order or []))
    if result.damage_profiles:
        melee = result.damage_profiles["Melee"]
        print("Melee total:", format_damage_range(total_damage_range(melee.noncrit)))
    print("Warnings:", len(result.warnings))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple Wynncraft build tester GUI.")
    parser.add_argument("--self-test", action="store_true", help="Run a non-GUI smoke test and exit.")
    args = parser.parse_args()

    engine = WynnBuildEngine(DATA_PATH)

    if args.self_test:
        return run_self_test(engine)

    app = WynnBuildTesterApp(engine)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
