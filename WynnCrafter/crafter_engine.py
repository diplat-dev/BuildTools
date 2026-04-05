from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

BASE64_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-"
BASE64_MAP = {char: idx for idx, char in enumerate(BASE64_DIGITS)}

SITE_RECIPE_ORDER = [
    "HELMET",
    "CHESTPLATE",
    "LEGGINGS",
    "BOOTS",
    "RELIK",
    "WAND",
    "SPEAR",
    "DAGGER",
    "BOW",
    "RING",
    "NECKLACE",
    "BRACELET",
    "POTION",
    "SCROLL",
    "FOOD",
]

SITE_LEVEL_ORDER = [
    "1-3",
    "3-5",
    "5-7",
    "7-9",
    "10-13",
    "13-15",
    "15-17",
    "17-19",
    "20-23",
    "23-25",
    "25-27",
    "27-29",
    "30-33",
    "33-35",
    "35-37",
    "37-39",
    "40-43",
    "43-45",
    "45-47",
    "47-49",
    "50-53",
    "53-55",
    "55-57",
    "57-59",
    "60-63",
    "63-65",
    "65-67",
    "67-69",
    "70-73",
    "73-75",
    "75-77",
    "77-79",
    "80-83",
    "83-85",
    "85-87",
    "87-89",
    "90-93",
    "93-95",
    "95-97",
    "97-99",
    "100-103",
    "103-105",
]

SKP_ORDER = ["str", "dex", "int", "def", "agi"]
SKP_ELEMENTS = ["e", "t", "w", "f", "a"]
ELEMENT_LABELS = {
    "n": "Neutral",
    "e": "Earth",
    "t": "Thunder",
    "w": "Water",
    "f": "Fire",
    "a": "Air",
}

ARMOR_TYPES = {"helmet", "chestplate", "leggings", "boots"}
ACCESSORY_TYPES = {"ring", "bracelet", "necklace"}
WEAPON_TYPES = {"wand", "spear", "bow", "dagger", "relik"}
CONSUMABLE_TYPES = {"potion", "scroll", "food"}

CRAFTED_ATK_SPEED = {"SLOW": 0, "NORMAL": 1, "FAST": 2}
CRAFTED_ATK_SPEED_ID = {value: key for key, value in CRAFTED_ATK_SPEED.items()}
CRAFTED_ENCODING_VERSION = 2
CRAFTED_VERSION_BITLEN = 7
ING_ID_BITLEN = 12
RECIPE_ID_BITLEN = 12
MAT_TIER_BITLEN = 3
ATK_SPEED_BITLEN = 4

ROLLED_IDS = [
    "hprPct",
    "mr",
    "sdPct",
    "mdPct",
    "ls",
    "ms",
    "xpb",
    "lb",
    "ref",
    "thorns",
    "expd",
    "spd",
    "atkTier",
    "poison",
    "hpBonus",
    "spRegen",
    "eSteal",
    "hprRaw",
    "sdRaw",
    "mdRaw",
    "fDamPct",
    "wDamPct",
    "aDamPct",
    "tDamPct",
    "eDamPct",
    "fDefPct",
    "wDefPct",
    "aDefPct",
    "tDefPct",
    "eDefPct",
    "spPct1",
    "spRaw1",
    "spPct2",
    "spRaw2",
    "spPct3",
    "spRaw3",
    "spPct4",
    "spRaw4",
    "rSdRaw",
    "sprint",
    "sprintReg",
    "jh",
    "lq",
    "gXp",
    "gSpd",
    "eMdPct",
    "eMdRaw",
    "eSdPct",
    "eSdRaw",
    "eDamRaw",
    "eDamAddMin",
    "eDamAddMax",
    "tMdPct",
    "tMdRaw",
    "tSdPct",
    "tSdRaw",
    "tDamRaw",
    "tDamAddMin",
    "tDamAddMax",
    "wMdPct",
    "wMdRaw",
    "wSdPct",
    "wSdRaw",
    "wDamRaw",
    "wDamAddMin",
    "wDamAddMax",
    "fMdPct",
    "fMdRaw",
    "fSdPct",
    "fSdRaw",
    "fDamRaw",
    "fDamAddMin",
    "fDamAddMax",
    "aMdPct",
    "aMdRaw",
    "aSdPct",
    "aSdRaw",
    "aDamRaw",
    "aDamAddMin",
    "aDamAddMax",
    "nMdPct",
    "nMdRaw",
    "nSdPct",
    "nSdRaw",
    "nDamPct",
    "nDamRaw",
    "nDamAddMin",
    "nDamAddMax",
    "damPct",
    "damRaw",
    "damAddMin",
    "damAddMax",
    "rMdPct",
    "rMdRaw",
    "rSdPct",
    "rDamPct",
    "rDamRaw",
    "rDamAddMin",
    "rDamAddMax",
    "critDamPct",
    "spPct1Final",
    "spPct2Final",
    "spPct3Final",
    "spPct4Final",
    "healPct",
    "kb",
    "weakenEnemy",
    "slowEnemy",
    "rDefPct",
    "maxMana",
    "mainAttackRange",
]

ING_FIELDS = ROLLED_IDS + ["str", "dex", "int", "def", "agi"]

DIRECT_STAT_LABELS = {
    "str": "Strength",
    "dex": "Dexterity",
    "int": "Intelligence",
    "def": "Defense",
    "agi": "Agility",
    "mr": "Mana Regen",
    "ms": "Mana Steal",
    "ls": "Life Steal",
    "lb": "Loot Bonus",
    "xpb": "XP Bonus",
    "ref": "Reflection",
    "thorns": "Thorns",
    "expd": "Exploding",
    "spd": "Walk Speed",
    "atkTier": "Attack Speed Tier",
    "poison": "Poison",
    "hpBonus": "Health Bonus",
    "spRegen": "Soul Point Regen",
    "eSteal": "Emerald Steal",
    "hprPct": "Health Regen %",
    "hprRaw": "Health Regen Raw",
    "sdPct": "Spell Damage %",
    "sdRaw": "Spell Damage Raw",
    "mdPct": "Main Attack Damage %",
    "mdRaw": "Main Attack Damage Raw",
    "sprint": "Sprint",
    "sprintReg": "Sprint Regen",
    "jh": "Jump Height",
    "lq": "Loot Quality",
    "gXp": "Gather XP Bonus",
    "gSpd": "Gather Speed",
    "damPct": "Damage %",
    "damRaw": "Damage Raw",
    "critDamPct": "Critical Damage %",
    "healPct": "Heal %",
    "kb": "Knockback",
    "weakenEnemy": "Weaken Enemy",
    "slowEnemy": "Slow Enemy",
    "rDefPct": "Elemental Defense %",
    "maxMana": "Max Mana",
    "mainAttackRange": "Main Attack Range",
    "durability": "Durability",
    "duration": "Duration",
    "charges": "Charges",
    "slots": "Slots",
    "hp": "Health",
}


@dataclass(frozen=True)
class Powder:
    min: int
    max: int
    convert: int
    def_plus: int
    def_minus: int


POWDER_STATS = [
    Powder(3, 6, 17, 2, 1),
    Powder(5, 8, 21, 4, 2),
    Powder(6, 10, 25, 8, 3),
    Powder(7, 10, 31, 14, 5),
    Powder(9, 11, 38, 22, 9),
    Powder(11, 13, 46, 30, 13),
    Powder(1, 8, 9, 3, 1),
    Powder(1, 12, 11, 5, 1),
    Powder(2, 15, 13, 9, 2),
    Powder(3, 15, 17, 14, 4),
    Powder(4, 17, 22, 20, 7),
    Powder(5, 20, 28, 28, 10),
    Powder(3, 4, 13, 3, 1),
    Powder(4, 6, 15, 6, 1),
    Powder(5, 8, 17, 11, 2),
    Powder(6, 8, 21, 18, 4),
    Powder(7, 10, 26, 28, 7),
    Powder(9, 11, 32, 40, 10),
    Powder(2, 5, 14, 3, 1),
    Powder(4, 8, 16, 5, 2),
    Powder(5, 9, 19, 9, 3),
    Powder(6, 9, 24, 16, 5),
    Powder(8, 10, 30, 25, 9),
    Powder(10, 12, 37, 36, 13),
    Powder(2, 6, 11, 3, 1),
    Powder(3, 10, 14, 6, 2),
    Powder(4, 11, 17, 10, 3),
    Powder(5, 11, 22, 16, 5),
    Powder(7, 12, 28, 24, 9),
    Powder(8, 14, 35, 34, 13),
]


@dataclass(frozen=True)
class Material:
    item: str
    amount: int


@dataclass(frozen=True)
class Ingredient:
    name: str
    display_name: str
    lvl: int
    tier: int
    skills: tuple[str, ...]
    min_rolls: dict[str, int]
    max_rolls: dict[str, int]
    item_ids: dict[str, float]
    consumable_ids: dict[str, int]
    pos_mods: dict[str, int]
    ingredient_id: int
    is_powder: bool = False
    pid: int | None = None

    @classmethod
    def from_raw(cls, raw: dict) -> "Ingredient":
        ids = raw.get("ids", {})
        min_rolls: dict[str, int] = {}
        max_rolls: dict[str, int] = {}
        for field in ING_FIELDS:
            roll = ids.get(field) or {}
            min_rolls[field] = int(roll.get("minimum", 0) or 0)
            max_rolls[field] = int(roll.get("maximum", 0) or 0)
        return cls(
            name=raw.get("name", ""),
            display_name=raw.get("displayName", raw.get("name", "")),
            lvl=int(raw.get("lvl", 0) or 0),
            tier=int(raw.get("tier", 0) or 0),
            skills=tuple(raw.get("skills", [])),
            min_rolls=min_rolls,
            max_rolls=max_rolls,
            item_ids={key: float(value) for key, value in raw.get("itemIDs", {}).items()},
            consumable_ids={key: int(value) for key, value in raw.get("consumableIDs", {}).items()},
            pos_mods={key: int(value) for key, value in raw.get("posMods", {}).items()},
            ingredient_id=int(raw.get("id", 0) or 0),
            is_powder=bool(raw.get("isPowder", False)),
            pid=raw.get("pid"),
        )


@dataclass(frozen=True)
class Recipe:
    name: str
    recipe_id: int
    type_name: str
    skill: str
    materials: tuple[Material, Material]
    health_or_damage: tuple[int, int]
    durability: tuple[int, int]
    duration: tuple[int, int]
    basic_duration: tuple[int, int]
    lvl: tuple[int, int]

    @property
    def display_type(self) -> str:
        return self.name.split("-", 1)[0]

    @property
    def level_range(self) -> str:
        return f"{self.lvl[0]}-{self.lvl[1]}"

    @property
    def type_key(self) -> str:
        return self.type_name.lower()

    @classmethod
    def from_raw(cls, raw: dict) -> "Recipe":
        def range_pair(key: str) -> tuple[int, int]:
            block = raw.get(key) or {}
            return int(block.get("minimum", 0) or 0), int(block.get("maximum", 0) or 0)

        materials = tuple(Material(item=entry["item"], amount=int(entry["amount"])) for entry in raw["materials"])
        return cls(
            name=raw["name"],
            recipe_id=int(raw["id"]),
            type_name=raw["type"],
            skill=raw["skill"],
            materials=(materials[0], materials[1]),
            health_or_damage=range_pair("healthOrDamage"),
            durability=range_pair("durability"),
            duration=range_pair("duration"),
            basic_duration=range_pair("basicDuration"),
            lvl=range_pair("lvl"),
        )


@dataclass(frozen=True)
class CraftSelection:
    recipe_name: str
    level_range: str
    mat_tiers: tuple[int, int]
    ingredient_names: tuple[str, str, str, str, str, str]
    attack_speed: str


@dataclass
class CraftResult:
    selection: CraftSelection
    recipe: Recipe
    ingredients: list[Ingredient]
    stat_map: dict
    hash_value: str
    warnings: list[str]
    ingredient_effectiveness: list[int]
    damage_rows: list[tuple[str, str, str]]

    @property
    def prefixed_hash(self) -> str:
        return f"CR-{self.hash_value}"


class BitWriter:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def append(self, value: int, bit_length: int) -> None:
        if bit_length < 0:
            raise ValueError("bit length must be non-negative")
        for idx in range(bit_length):
            self.bits.append((value >> idx) & 1)

    def to_b64(self) -> str:
        chars: list[str] = []
        for start in range(0, len(self.bits), 6):
            chunk = self.bits[start : start + 6]
            value = 0
            for idx, bit in enumerate(chunk):
                value |= bit << idx
            chars.append(BASE64_DIGITS[value])
        return "".join(chars)


class BitReader:
    def __init__(self, b64_text: str) -> None:
        self.bits: list[int] = []
        for char in b64_text:
            if char not in BASE64_MAP:
                raise ValueError(f"invalid base64 character: {char!r}")
            value = BASE64_MAP[char]
            for idx in range(6):
                self.bits.append((value >> idx) & 1)
        self.index = 0

    def read(self, bit_length: int = 1) -> int:
        if self.index + bit_length > len(self.bits):
            raise ValueError("hash ended unexpectedly")
        value = 0
        for idx in range(bit_length):
            value |= self.bits[self.index + idx] << idx
        self.index += bit_length
        return value

    def skip(self, bit_length: int) -> None:
        if self.index + bit_length > len(self.bits):
            raise ValueError("hash ended unexpectedly")
        self.index += bit_length


class CrafterData:
    def __init__(self, ingredients: Iterable[Ingredient], recipes: Iterable[Recipe]) -> None:
        self.ingredients = list(ingredients)
        self.recipes = list(recipes)

        self.ingredients_by_name = {ingredient.display_name: ingredient for ingredient in self.ingredients}
        self.ingredients_by_id = {ingredient.ingredient_id: ingredient for ingredient in self.ingredients}
        self.ingredients_by_name_casefold = {
            ingredient.display_name.casefold(): ingredient.display_name for ingredient in self.ingredients
        }

        self.recipes_by_name = {recipe.name: recipe for recipe in self.recipes}
        self.recipes_by_id = {recipe.recipe_id: recipe for recipe in self.recipes}
        self.recipe_names_casefold = {recipe.name.casefold(): recipe.name for recipe in self.recipes}

        self.ingredient_display_names = sorted(
            self.ingredients_by_name,
            key=lambda name: (name != "No Ingredient", name.casefold()),
        )

        known_recipe_types = {recipe.display_type for recipe in self.recipes}
        self.recipe_type_names = [
            title_case(recipe_type)
            for recipe_type in SITE_RECIPE_ORDER
            if title_case(recipe_type) in known_recipe_types
        ]
        for recipe_type in sorted(known_recipe_types, key=str.casefold):
            if recipe_type not in self.recipe_type_names:
                self.recipe_type_names.append(recipe_type)

        known_level_ranges = {recipe.level_range for recipe in self.recipes}
        self.level_ranges = [level for level in SITE_LEVEL_ORDER if level in known_level_ranges]
        for level in sorted(known_level_ranges, key=lambda value: tuple(int(part) for part in value.split("-"))):
            if level not in self.level_ranges:
                self.level_ranges.append(level)

    @classmethod
    def load(cls, data_dir: Path = DATA_DIR) -> "CrafterData":
        ingredient_path = data_dir / "ingreds_compress.json"
        recipe_path = data_dir / "recipes_compress.json"

        ingredients_raw = json.loads(ingredient_path.read_text(encoding="utf-8"))
        recipes_payload = json.loads(recipe_path.read_text(encoding="utf-8"))
        recipes_raw = recipes_payload["recipes"]

        ingredients = [build_no_ingredient(), *build_powder_ingredients()]
        ingredients.extend(Ingredient.from_raw(raw) for raw in ingredients_raw)
        recipes = [Recipe.from_raw(raw) for raw in recipes_raw]
        return cls(ingredients=ingredients, recipes=recipes)

    def default_selection(self) -> CraftSelection:
        return CraftSelection(
            recipe_name="Potion",
            level_range="103-105",
            mat_tiers=(3, 3),
            ingredient_names=("No Ingredient",) * 6,
            attack_speed="NORMAL",
        )

    def resolve_ingredient_name(self, name: str) -> str:
        candidate = (name or "").strip()
        if not candidate:
            return "No Ingredient"
        exact = self.ingredients_by_name.get(candidate)
        if exact is not None:
            return exact.display_name
        normalized = self.ingredients_by_name_casefold.get(candidate.casefold())
        if normalized is None:
            raise ValueError(f"Unknown ingredient: {candidate}")
        return normalized

    def get_recipe(self, recipe_name: str, level_range: str) -> Recipe:
        key = f"{recipe_name.strip()}-{level_range.strip()}"
        recipe = self.recipes_by_name.get(key)
        if recipe is not None:
            return recipe
        normalized = self.recipe_names_casefold.get(key.casefold())
        if normalized is None:
            raise ValueError(f"Unknown recipe: {recipe_name} {level_range}")
        return self.recipes_by_name[normalized]

    def craft(self, selection: CraftSelection) -> CraftResult:
        recipe = self.get_recipe(selection.recipe_name, selection.level_range)
        ingredient_names = tuple(self.resolve_ingredient_name(name) for name in selection.ingredient_names)
        if len(ingredient_names) != 6:
            raise ValueError("Exactly six ingredient slots are required")
        ingredients = [self.ingredients_by_name[name] for name in ingredient_names]
        mat_tiers = tuple(int(tier) for tier in selection.mat_tiers)
        if len(mat_tiers) != 2 or any(tier not in (1, 2, 3) for tier in mat_tiers):
            raise ValueError("Material tiers must be 1, 2, or 3")

        attack_speed = selection.attack_speed.upper()
        if attack_speed not in CRAFTED_ATK_SPEED:
            raise ValueError(f"Invalid attack speed: {selection.attack_speed}")

        stat_map = self._build_stat_map(recipe, ingredients, mat_tiers, attack_speed)
        hash_value = self.encode_hash(recipe, ingredients, mat_tiers, attack_speed, stat_map["category"])
        stat_map["name"] = f"CR-{hash_value}"
        stat_map["displayName"] = f"CR-{hash_value}"
        stat_map["hash"] = f"CR-{hash_value}"

        warnings = self._build_warnings(recipe, ingredients)
        ingredient_effectiveness = list(stat_map.get("ingredEffectiveness", [100] * 6))
        damage_rows = self._build_damage_rows(stat_map)

        final_selection = CraftSelection(
            recipe_name=recipe.display_type,
            level_range=recipe.level_range,
            mat_tiers=mat_tiers,
            ingredient_names=ingredient_names,
            attack_speed=attack_speed,
        )
        return CraftResult(
            selection=final_selection,
            recipe=recipe,
            ingredients=ingredients,
            stat_map=stat_map,
            hash_value=hash_value,
            warnings=warnings,
            ingredient_effectiveness=ingredient_effectiveness,
            damage_rows=damage_rows,
        )

    def encode_hash(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        mat_tiers: tuple[int, int],
        attack_speed: str,
        category: str,
    ) -> str:
        writer = BitWriter()
        writer.append(0, 1)
        writer.append(CRAFTED_ENCODING_VERSION, CRAFTED_VERSION_BITLEN)
        for ingredient in ingredients:
            writer.append(ingredient.ingredient_id, ING_ID_BITLEN)
        writer.append(recipe.recipe_id, RECIPE_ID_BITLEN)
        for tier in mat_tiers:
            writer.append(tier - 1, MAT_TIER_BITLEN)
        if category == "weapon":
            writer.append(CRAFTED_ATK_SPEED[attack_speed], ATK_SPEED_BITLEN)
        pad_bits = 6 - (len(writer.bits) % 6)
        writer.append(0, pad_bits)
        return writer.to_b64()

    def decode_hash_to_selection(self, hash_text: str) -> CraftSelection:
        normalized = normalize_hash(hash_text)
        if not normalized:
            raise ValueError("Hash is empty")
        if BASE64_MAP[normalized[0]] & 0x1:
            return self._decode_legacy_hash(normalized)

        reader = BitReader(normalized)
        legacy = reader.read(1)
        if legacy:
            return self._decode_legacy_hash(normalized)

        _version = reader.read(CRAFTED_VERSION_BITLEN)
        ingredients = [self.ingredients_by_id[reader.read(ING_ID_BITLEN)].display_name for _ in range(6)]
        recipe = self.recipes_by_id[reader.read(RECIPE_ID_BITLEN)]
        mat_tiers = tuple(reader.read(MAT_TIER_BITLEN) + 1 for _ in range(2))
        attack_speed = "SLOW"
        if recipe.type_key in WEAPON_TYPES:
            attack_speed_id = reader.read(ATK_SPEED_BITLEN)
            attack_speed = CRAFTED_ATK_SPEED_ID.get(attack_speed_id, "SLOW")
        padding = 6 - (reader.index % 6)
        reader.skip(padding)
        return CraftSelection(
            recipe_name=recipe.display_type,
            level_range=recipe.level_range,
            mat_tiers=mat_tiers,
            ingredient_names=tuple(ingredients),
            attack_speed=attack_speed,
        )

    def _decode_legacy_hash(self, normalized_hash: str) -> CraftSelection:
        if len(normalized_hash) < 17:
            raise ValueError("Legacy craft hash is too short")
        version = normalized_hash[0]
        if version != "1":
            raise ValueError(f"Unsupported legacy craft version: {version}")
        payload = normalized_hash[1:]
        ingredients = [
            self.ingredients_by_id[b64_to_int(payload[2 * idx : 2 * idx + 2])].display_name
            for idx in range(6)
        ]
        recipe = self.recipes_by_id[b64_to_int(payload[12:14])]
        tier_num = b64_to_int(payload[14:15])
        mat_1 = 3 if tier_num % 3 == 0 else tier_num % 3
        mat_2 = math.floor((tier_num - 0.5) / 3) + 1
        attack_speed_id = b64_to_int(payload[15:16])
        attack_speed = ["SLOW", "NORMAL", "FAST"][attack_speed_id]
        return CraftSelection(
            recipe_name=recipe.display_type,
            level_range=recipe.level_range,
            mat_tiers=(mat_1, mat_2),
            ingredient_names=tuple(ingredients),
            attack_speed=attack_speed,
        )

    def _build_warnings(self, recipe: Recipe, ingredients: list[Ingredient]) -> list[str]:
        warnings: list[str] = []
        max_level = recipe.lvl[1]
        readable_skill = title_case(recipe.skill)
        for ingredient in ingredients:
            if recipe.skill not in ingredient.skills:
                warnings.append(f"{ingredient.display_name} cannot be used for {readable_skill}.")
            if ingredient.lvl > max_level:
                warnings.append(
                    f"{ingredient.display_name} is too high level for range {recipe.level_range}."
                )
        return warnings

    def _build_stat_map(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        mat_tiers: tuple[int, int],
        attack_speed: str,
    ) -> dict:
        stat_map: dict = {
            "minRolls": {},
            "maxRolls": {},
            "name": "CR-",
            "displayName": "CR-",
            "tier": "Crafted",
            "type": recipe.type_key,
            "duration": [recipe.duration[0], recipe.duration[1]],
            "durability": [recipe.durability[0], recipe.durability[1]],
            "lvl": recipe.lvl[1],
            "lvlLow": recipe.lvl[0],
            "nDam": 0,
            "hp": 0,
            "hpLow": 0,
            "powders": [],
        }

        for element in SKP_ELEMENTS:
            stat_map[f"{element}Dam"] = "0-0"
            stat_map[f"{element}Def"] = 0
        for skill in SKP_ORDER:
            stat_map[f"{skill}Req"] = 0
            stat_map[skill] = 0

        item_type = recipe.type_key
        all_none = all(ingredient.name == "No Ingredient" for ingredient in ingredients)

        if item_type in ARMOR_TYPES or item_type in WEAPON_TYPES:
            stat_map["slots"] = 1 if recipe.lvl[0] < 30 else 2 if recipe.lvl[0] < 70 else 3
        else:
            stat_map["slots"] = 0

        if item_type in CONSUMABLE_TYPES:
            stat_map["category"] = "consumable"
            stat_map["charges"] = 1 if recipe.lvl[0] < 30 else 2 if recipe.lvl[0] < 70 else 3
            if all_none:
                stat_map["charges"] = 3
                stat_map["hp"] = format_pair(recipe.health_or_damage)
                stat_map["duration"] = [recipe.basic_duration[0], recipe.basic_duration[1]]
        else:
            stat_map["charges"] = 0

        if item_type in ARMOR_TYPES:
            stat_map["hp"] = format_pair(recipe.health_or_damage)
            stat_map["category"] = "armor"
        elif item_type in WEAPON_TYPES:
            stat_map["nDam"] = format_pair(recipe.health_or_damage)
            for element in SKP_ELEMENTS:
                stat_map[f"{element}Dam"] = "0-0"
                stat_map[f"{element}DamLow"] = "0-0"
            stat_map["category"] = "weapon"
            stat_map["atkSpd"] = attack_speed
        elif item_type in ACCESSORY_TYPES:
            stat_map["category"] = "accessory"

        tier_to_mult = [0, 1.0, 1.25, 1.4]
        amounts = [recipe.materials[0].amount, recipe.materials[1].amount]
        material_multiplier = (
            tier_to_mult[mat_tiers[0]] * amounts[0] + tier_to_mult[mat_tiers[1]] * amounts[1]
        ) / (amounts[0] + amounts[1])

        base_low, base_high = recipe.health_or_damage
        if stat_map["category"] == "consumable":
            if all_none:
                stat_map["hp"] = f"{math.floor(base_low * material_multiplier)}-{math.floor(base_high * material_multiplier)}"
            stat_map["duration"] = [
                round(stat_map["duration"][0] * material_multiplier),
                round(stat_map["duration"][1] * material_multiplier),
            ]
        else:
            stat_map["durability"] = [
                round(stat_map["durability"][0] * material_multiplier),
                round(stat_map["durability"][1] * material_multiplier),
            ]

        if stat_map["category"] == "weapon":
            ratio = 2.05
            if attack_speed == "SLOW":
                ratio /= 1.5
            elif attack_speed == "NORMAL":
                ratio = 1.0
            elif attack_speed == "FAST":
                ratio /= 2.5

            neutral_base_low = math.floor(math.floor(base_low * material_multiplier) * ratio)
            neutral_base_high = math.floor(math.floor(base_high * material_multiplier) * ratio)

            powders: list[int] = []
            for ingredient in ingredients:
                if ingredient.is_powder and ingredient.pid is not None:
                    powders.append(ingredient.pid)
            stat_map["ingredPowders"] = powders

            stat_map["nDamBaseLow"] = neutral_base_low
            stat_map["nDamBaseHigh"] = neutral_base_high
            stat_map["nDamLow"] = f"{math.floor(neutral_base_low * 0.9)}-{math.floor(neutral_base_low * 1.1)}"
            stat_map["nDam"] = f"{math.floor(neutral_base_high * 0.9)}-{math.floor(neutral_base_high * 1.1)}"

            for element in SKP_ELEMENTS:
                stat_map[f"{element}DamBaseLow"] = 0
                stat_map[f"{element}DamBaseHigh"] = 0
                stat_map[f"{element}DamLow"] = "0-0"
                stat_map[f"{element}Dam"] = "0-0"

        elif stat_map["category"] == "armor":
            low_hp = math.floor(base_low * material_multiplier)
            high_hp = math.floor(base_high * material_multiplier)
            stat_map["hp"] = high_hp
            stat_map["hpLow"] = low_hp

        if stat_map["category"] in {"armor", "accessory"}:
            for ingredient in ingredients:
                if not ingredient.is_powder or ingredient.pid is None:
                    continue
                powder = POWDER_STATS[ingredient.pid]
                element = SKP_ELEMENTS[ingredient.pid // 6]
                previous = SKP_ELEMENTS[(SKP_ELEMENTS.index(element) + 4) % 5]
                stat_map[f"{element}Def"] = int(stat_map.get(f"{element}Def", 0) + powder.def_plus)
                stat_map[f"{previous}Def"] = int(stat_map.get(f"{previous}Def", 0) - powder.def_minus)

        effectiveness = [[100, 100], [100, 100], [100, 100]]
        for idx, ingredient in enumerate(ingredients):
            row = idx // 2
            col = idx % 2
            for key, value in ingredient.pos_mods.items():
                if value == 0:
                    continue
                if key == "above":
                    for target_row in range(row - 1, -1, -1):
                        effectiveness[target_row][col] += value
                elif key == "under":
                    for target_row in range(row + 1, 3):
                        effectiveness[target_row][col] += value
                elif key == "left" and col == 1:
                    effectiveness[row][0] += value
                elif key == "right" and col == 0:
                    effectiveness[row][1] += value
                elif key == "touching":
                    for target_row in range(3):
                        for target_col in range(2):
                            if (abs(target_row - row) == 1 and abs(target_col - col) == 0) or (
                                abs(target_row - row) == 0 and abs(target_col - col) == 1
                            ):
                                effectiveness[target_row][target_col] += value
                elif key == "notTouching":
                    for target_row in range(3):
                        for target_col in range(2):
                            if abs(target_row - row) > 1 or (
                                abs(target_row - row) == 1 and abs(target_col - col) == 1
                            ):
                                effectiveness[target_row][target_col] += value

        flat_effectiveness = [cell for row in effectiveness for cell in row]
        stat_map["ingredEffectiveness"] = flat_effectiveness

        min_rolls: dict[str, int] = {}
        max_rolls: dict[str, int] = {}
        stat_map["minRolls"] = min_rolls
        stat_map["maxRolls"] = max_rolls

        for idx, ingredient in enumerate(ingredients):
            effect_multiplier = float(f"{flat_effectiveness[idx] / 100:.2f}")

            for key, value in ingredient.item_ids.items():
                if key != "dura" and item_type not in CONSUMABLE_TYPES:
                    current = stat_map.get(key, 0)
                    if not ingredient.is_powder:
                        stat_map[key] = int(round(current + value * effect_multiplier))
                    else:
                        stat_map[key] = int(round(current + value))
                else:
                    stat_map["durability"] = [entry + value for entry in stat_map["durability"]]

            for key, value in ingredient.consumable_ids.items():
                if key == "dura":
                    stat_map["duration"] = [entry + value for entry in stat_map["duration"]]
                else:
                    stat_map[key] = int(stat_map.get(key, 0) + value)

            for key in ING_FIELDS:
                max_value = ingredient.max_rolls.get(key, 0)
                if not max_value:
                    continue
                min_value = ingredient.min_rolls.get(key, 0)
                rolls = sorted(
                    (
                        math.floor(min_value * effect_multiplier),
                        math.floor(max_value * effect_multiplier),
                    )
                )
                min_rolls[key] = min_rolls.get(key, 0) + rolls[0]
                max_rolls[key] = max_rolls.get(key, 0) + rolls[1]

        stat_map["durability"] = [
            1 if entry < 1 else math.floor(entry)
            for entry in stat_map["durability"]
        ]
        stat_map["duration"] = [
            10 if not all_none and entry < 10 else int(entry)
            for entry in stat_map["duration"]
        ]
        if stat_map.get("charges", 0) < 1:
            stat_map["charges"] = 1

        stat_map["reqs"] = [0, 0, 0, 0, 0]
        stat_map["skillpoints"] = [0, 0, 0, 0, 0]
        for idx, skill in enumerate(SKP_ORDER):
            stat_map[skill] = int(max_rolls.get(skill, 0))
            stat_map["skillpoints"][idx] = int(max_rolls.get(skill, 0))
            stat_map["reqs"][idx] = int(stat_map.get(f"{skill}Req", 0) if item_type not in CONSUMABLE_TYPES else 0)

        for stat_id in ROLLED_IDS:
            min_rolls.setdefault(stat_id, 0)
            max_rolls.setdefault(stat_id, 0)

        stat_map["crafted"] = True
        return stat_map

    def _build_damage_rows(self, stat_map: dict) -> list[tuple[str, str, str]]:
        if stat_map.get("category") != "weapon":
            return []

        low_bases = [
            stat_map.get("nDamBaseLow", 0),
            stat_map.get("eDamBaseLow", 0),
            stat_map.get("tDamBaseLow", 0),
            stat_map.get("wDamBaseLow", 0),
            stat_map.get("fDamBaseLow", 0),
            stat_map.get("aDamBaseLow", 0),
        ]
        high_bases = [
            stat_map.get("nDamBaseHigh", 0),
            stat_map.get("eDamBaseHigh", 0),
            stat_map.get("tDamBaseHigh", 0),
            stat_map.get("wDamBaseHigh", 0),
            stat_map.get("fDamBaseHigh", 0),
            stat_map.get("aDamBaseHigh", 0),
        ]

        low_damage, _ = self._calc_weapon_powder(stat_map, low_bases)
        high_damage, present = self._calc_weapon_powder(stat_map, high_bases)

        element_order = ["n", "e", "t", "w", "f", "a"]
        rows: list[tuple[str, str, str]] = []
        for idx, element in enumerate(element_order):
            if not present[idx]:
                continue
            rows.append(
                (
                    ELEMENT_LABELS[element],
                    format_damage_range(low_damage[idx]),
                    format_damage_range(high_damage[idx]),
                )
            )
        return rows

    def _calc_weapon_powder(self, stat_map: dict, damage_bases: list[int]) -> tuple[list[list[float]], list[bool]]:
        damages: list[list[float]] = [
            [float(entry) for entry in parse_range(stat_map.get("nDam", "0-0"))],
            [float(entry) for entry in parse_range(stat_map.get("eDam", "0-0"))],
            [float(entry) for entry in parse_range(stat_map.get("tDam", "0-0"))],
            [float(entry) for entry in parse_range(stat_map.get("wDam", "0-0"))],
            [float(entry) for entry in parse_range(stat_map.get("fDam", "0-0"))],
            [float(entry) for entry in parse_range(stat_map.get("aDam", "0-0"))],
        ]

        if damage_bases is not None:
            damages[0] = [math.floor(damage_bases[0] * 0.9), math.floor(damage_bases[0] * 1.1)]

        neutral_remaining = damages[0][:]
        powder_apply_order: list[int] = []
        powder_apply_map: dict[int, dict[str, float]] = {}

        for powder_id in list(stat_map.get("powders", [])):
            powder = POWDER_STATS[powder_id]
            element = powder_id // 6
            apply_info = powder_apply_map.setdefault(
                element,
                {"conv": 0.0, "min": 0.0, "max": 0.0},
            )
            if element not in powder_apply_order:
                powder_apply_order.append(element)
            apply_info["conv"] += powder.convert / 100
            apply_info["min"] += powder.min
            apply_info["max"] += powder.max

        if stat_map.get("tier") == "Crafted" and not stat_map.get("custom"):
            for powder_id in stat_map.get("ingredPowders", []):
                powder = POWDER_STATS[powder_id]
                element = powder_id // 6
                apply_info = powder_apply_map.setdefault(
                    element,
                    {"conv": 0.0, "min": 0.0, "max": 0.0},
                )
                if element not in powder_apply_order:
                    powder_apply_order.append(element)
                apply_info["conv"] += powder.convert / 100 / 2
                apply_info["min"] += math.floor(powder.min / 2)
                apply_info["max"] += math.floor(powder.max / 2)

        for element in powder_apply_order:
            apply_info = powder_apply_map[element]
            min_diff = min(neutral_remaining[0], apply_info["conv"] * neutral_remaining[0])
            max_diff = min(neutral_remaining[1], apply_info["conv"] * neutral_remaining[1])
            neutral_remaining[0] -= min_diff
            neutral_remaining[1] -= max_diff
            damages[element + 1][0] += min_diff + apply_info["min"]
            damages[element + 1][1] += max_diff + apply_info["max"]

        damages[0] = neutral_remaining
        present = [damage[1] > 0 for damage in damages]
        return damages, present


def build_no_ingredient() -> Ingredient:
    raw = {
        "name": "No Ingredient",
        "displayName": "No Ingredient",
        "tier": 0,
        "lvl": 0,
        "skills": [
            "ARMOURING",
            "TAILORING",
            "WEAPONSMITHING",
            "WOODWORKING",
            "JEWELING",
            "COOKING",
            "ALCHEMISM",
            "SCRIBING",
        ],
        "ids": {},
        "itemIDs": {
            "dura": 0,
            "strReq": 0,
            "dexReq": 0,
            "intReq": 0,
            "defReq": 0,
            "agiReq": 0,
        },
        "consumableIDs": {"dura": 0, "charges": 0},
        "posMods": {
            "left": 0,
            "right": 0,
            "above": 0,
            "under": 0,
            "touching": 0,
            "notTouching": 0,
        },
        "id": 4000,
    }
    return Ingredient.from_raw(raw)


def build_powder_ingredients() -> list[Ingredient]:
    numerals = ["I", "II", "III", "IV", "V", "VI"]
    element_names = ["Earth", "Thunder", "Water", "Fire", "Air"]
    powder_ing_info = [(-35, 0), (-52.5, 0), (-70, 10), (-91, 20), (-112, 28), (-133, 36)]

    ingredients: list[Ingredient] = []
    for element_idx, element_name in enumerate(element_names):
        for tier_idx, (durability_delta, req_delta) in enumerate(powder_ing_info):
            raw = {
                "name": f"{element_name} Powder {numerals[tier_idx]}",
                "displayName": f"{element_name} Powder {numerals[tier_idx]}",
                "tier": 0,
                "lvl": 0,
                "skills": [
                    "ARMOURING",
                    "TAILORING",
                    "WEAPONSMITHING",
                    "WOODWORKING",
                    "JEWELING",
                ],
                "ids": {},
                "isPowder": True,
                "pid": 6 * element_idx + tier_idx,
                "itemIDs": {
                    "dura": durability_delta,
                    "strReq": 0,
                    "dexReq": 0,
                    "intReq": 0,
                    "defReq": 0,
                    "agiReq": 0,
                },
                "consumableIDs": {"dura": 0, "charges": 0},
                "posMods": {
                    "left": 0,
                    "right": 0,
                    "above": 0,
                    "under": 0,
                    "touching": 0,
                    "notTouching": 0,
                },
                "id": 4001 + (6 * element_idx + tier_idx),
            }
            raw["itemIDs"][f"{SKP_ORDER[element_idx]}Req"] = req_delta
            ingredients.append(Ingredient.from_raw(raw))
    return ingredients


def normalize_hash(hash_text: str) -> str:
    normalized = hash_text.strip()
    if normalized.startswith("#"):
        normalized = normalized[1:]
    if normalized.startswith("CR-"):
        normalized = normalized[3:]
    if not normalized:
        return ""
    for char in normalized:
        if char not in BASE64_MAP:
            raise ValueError(f"Hash contains an invalid character: {char!r}")
    return normalized


def b64_to_int(text: str) -> int:
    value = 0
    for char in text:
        value = (value << 6) + BASE64_MAP[char]
    return value


def title_case(value: str) -> str:
    return value[:1] + value[1:].lower() if value else value


def parse_range(value: str | int | float) -> tuple[int, int]:
    if isinstance(value, (int, float)):
        int_value = int(value)
        return int_value, int_value
    parts = str(value).split("-", 1)
    if len(parts) == 1:
        number = int(parts[0])
        return number, number
    return int(parts[0]), int(parts[1])


def format_pair(pair: tuple[int, int]) -> str:
    return f"{pair[0]}-{pair[1]}"


def format_damage_range(values: list[float]) -> str:
    low = math.floor(values[0])
    high = math.floor(values[1])
    return f"{low}-{high}"


def humanize_stat_key(key: str) -> str:
    direct = DIRECT_STAT_LABELS.get(key)
    if direct is not None:
        return direct

    if key.endswith("Req"):
        return f"{humanize_stat_key(key[:-3])} Req"

    patterns = [
        ("DamPct", "Damage %"),
        ("DamRaw", "Damage Raw"),
        ("DamAddMin", "Damage Add Min"),
        ("DamAddMax", "Damage Add Max"),
        ("MdPct", "Main Attack Damage %"),
        ("MdRaw", "Main Attack Damage Raw"),
        ("SdPct", "Spell Damage %"),
        ("SdRaw", "Spell Damage Raw"),
        ("DefPct", "Defense %"),
        ("Def", "Defense"),
    ]

    element_prefixes = {
        "n": "Neutral",
        "e": "Earth",
        "t": "Thunder",
        "w": "Water",
        "f": "Fire",
        "a": "Air",
        "r": "Rainbow",
    }

    for prefix, element_name in element_prefixes.items():
        if not key.startswith(prefix):
            continue
        remainder = key[len(prefix) :]
        for suffix, label in patterns:
            if remainder == suffix:
                return f"{element_name} {label}"

    return key


def format_roll(minimum: int, maximum: int) -> str:
    if minimum == maximum:
        return str(minimum)
    return f"{minimum} to {maximum}"


def nonzero_stats(items: Iterable[tuple[str, int | float]]) -> list[tuple[str, int | float]]:
    return [(key, value) for key, value in items if value]


def format_recipe_summary(result: CraftResult) -> str:
    recipe = result.recipe
    lines = [
        f"{recipe.display_type} {recipe.level_range}",
        f"Skill: {title_case(recipe.skill)}",
        f"Materials: {recipe.materials[0].item} x{recipe.materials[0].amount}, {recipe.materials[1].item} x{recipe.materials[1].amount}",
        f"Material tiers: {result.selection.mat_tiers[0]}, {result.selection.mat_tiers[1]}",
    ]

    if recipe.type_key in CONSUMABLE_TYPES:
        lines.append(f"Base effect: {format_pair(recipe.health_or_damage)}")
        lines.append(f"Base duration: {format_pair(recipe.duration)}")
        lines.append(f"Basic duration: {format_pair(recipe.basic_duration)}")
    elif recipe.type_key in WEAPON_TYPES:
        lines.append(f"Base damage: {format_pair(recipe.health_or_damage)}")
        lines.append(f"Base durability: {format_pair(recipe.durability)}")
    elif recipe.type_key in ARMOR_TYPES:
        lines.append(f"Base health: {format_pair(recipe.health_or_damage)}")
        lines.append(f"Base durability: {format_pair(recipe.durability)}")
    else:
        lines.append(f"Base durability: {format_pair(recipe.durability)}")

    return "\n".join(lines)


def format_craft_summary(result: CraftResult) -> str:
    stat_map = result.stat_map
    lines = [
        f"Hash: {result.prefixed_hash}",
        f"Category: {title_case(stat_map['category'])}",
        f"Type: {title_case(stat_map['type'])}",
        f"Level: {stat_map['lvlLow']}-{stat_map['lvl']}",
    ]

    if stat_map["category"] == "weapon":
        lines.append(f"Attack speed: {result.selection.attack_speed}")
        lines.append(f"Slots: {stat_map['slots']}")
        lines.append(
            f"Durability: {stat_map['durability'][0]}-{stat_map['durability'][1]}"
        )
        if result.damage_rows:
            lines.append("")
            lines.append("Damage (low roll | high roll):")
            for label, low_text, high_text in result.damage_rows:
                lines.append(f"- {label}: {low_text} | {high_text}")
    elif stat_map["category"] == "armor":
        lines.append(f"Slots: {stat_map['slots']}")
        lines.append(
            f"Durability: {stat_map['durability'][0]}-{stat_map['durability'][1]}"
        )
        lines.append(f"Health: {stat_map['hpLow']}-{stat_map['hp']}")
    elif stat_map["category"] == "accessory":
        lines.append(
            f"Durability: {stat_map['durability'][0]}-{stat_map['durability'][1]}"
        )
    elif stat_map["category"] == "consumable":
        lines.append(f"Charges: {stat_map['charges']}")
        lines.append(f"Duration: {stat_map['duration'][0]}-{stat_map['duration'][1]}")
        if stat_map.get("hp"):
            lines.append(f"Base effect: {stat_map['hp']}")

    defenses = nonzero_stats((f"{element}Def", stat_map.get(f"{element}Def", 0)) for element in SKP_ELEMENTS)
    if defenses:
        lines.append("")
        lines.append("Defenses:")
        for key, value in defenses:
            lines.append(f"- {humanize_stat_key(key)}: {int(value)}")

    requirements = [(skill, stat_map["reqs"][idx]) for idx, skill in enumerate(SKP_ORDER) if stat_map["reqs"][idx]]
    if requirements:
        lines.append("")
        lines.append("Requirements:")
        for key, value in requirements:
            lines.append(f"- {humanize_stat_key(key)}: {value}")

    skill_rolls = [
        (skill, stat_map["minRolls"].get(skill, 0), stat_map["maxRolls"].get(skill, 0))
        for skill in SKP_ORDER
        if stat_map["minRolls"].get(skill, 0) or stat_map["maxRolls"].get(skill, 0)
    ]
    if skill_rolls:
        lines.append("")
        lines.append("Skill bonuses:")
        for key, minimum, maximum in skill_rolls:
            lines.append(f"- {humanize_stat_key(key)}: {format_roll(minimum, maximum)}")

    rolled = [
        (stat_id, stat_map["minRolls"].get(stat_id, 0), stat_map["maxRolls"].get(stat_id, 0))
        for stat_id in ROLLED_IDS
        if stat_map["minRolls"].get(stat_id, 0) or stat_map["maxRolls"].get(stat_id, 0)
    ]
    if rolled:
        lines.append("")
        lines.append("Rolled IDs:")
        for stat_id, minimum, maximum in rolled:
            lines.append(f"- {humanize_stat_key(stat_id)}: {format_roll(minimum, maximum)}")

    effectiveness = result.ingredient_effectiveness
    if effectiveness:
        lines.append("")
        lines.append("Ingredient effectiveness:")
        for idx, value in enumerate(effectiveness, start=1):
            lines.append(f"- Slot {idx}: {value}%")

    return "\n".join(lines)


def format_warnings(result: CraftResult) -> str:
    if not result.warnings:
        return "No warnings."
    return "\n".join(f"- {warning}" for warning in result.warnings)


def format_ingredient_summary(result: CraftResult) -> str:
    sections: list[str] = []
    for idx, ingredient in enumerate(result.ingredients, start=1):
        lines = [
            f"Slot {idx}: {ingredient.display_name}",
            f"Level: {ingredient.lvl}",
            f"Tier: {ingredient.tier}",
            f"Skills: {', '.join(title_case(skill) for skill in ingredient.skills)}",
            f"Effectiveness: {result.ingredient_effectiveness[idx - 1]}%",
        ]

        item_ids = nonzero_stats(ingredient.item_ids.items())
        if item_ids:
            lines.append("Item IDs:")
            for key, value in item_ids:
                number = int(value) if float(value).is_integer() else value
                lines.append(f"- {humanize_stat_key(key)}: {number}")

        consumable_ids = nonzero_stats(ingredient.consumable_ids.items())
        if consumable_ids:
            lines.append("Consumable IDs:")
            for key, value in consumable_ids:
                lines.append(f"- {humanize_stat_key(key)}: {value}")

        pos_mods = nonzero_stats(ingredient.pos_mods.items())
        if pos_mods:
            lines.append("Position modifiers:")
            for key, value in pos_mods:
                lines.append(f"- {key}: {value}")

        rolls = [
            (key, ingredient.min_rolls.get(key, 0), ingredient.max_rolls.get(key, 0))
            for key in ING_FIELDS
            if ingredient.min_rolls.get(key, 0) or ingredient.max_rolls.get(key, 0)
        ]
        if rolls:
            lines.append("Rolls:")
            for key, minimum, maximum in rolls:
                lines.append(f"- {humanize_stat_key(key)}: {format_roll(minimum, maximum)}")

        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def build_copy_short(result: CraftResult) -> str:
    ingredients = " | ".join(result.selection.ingredient_names)
    return (
        f"{result.recipe.display_type} {result.recipe.level_range} "
        f"({result.selection.mat_tiers[0]}*, {result.selection.mat_tiers[1]}*) "
        f"| {ingredients} | {result.prefixed_hash}"
    )


def build_copy_long(result: CraftResult) -> str:
    ingredient_names = list(result.selection.ingredient_names)
    return "\n".join(
        [
            result.prefixed_hash,
            f"> {result.recipe.display_type} Lv. {result.recipe.level_range} ({result.selection.mat_tiers[0]}*, {result.selection.mat_tiers[1]}*)",
            f"> [{ingredient_names[0]} | {ingredient_names[1]}",
            f">  {ingredient_names[2]} | {ingredient_names[3]}",
            f">  {ingredient_names[4]} | {ingredient_names[5]}]",
        ]
    )
