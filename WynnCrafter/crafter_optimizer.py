from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

from crafter_engine import (
    ACCESSORY_TYPES,
    ARMOR_TYPES,
    CONSUMABLE_TYPES,
    POWDER_STATS,
    ROLLED_IDS,
    SKP_ORDER,
    SKP_ELEMENTS,
    CrafterData,
    CraftResult,
    CraftSelection,
    Ingredient,
    Recipe,
    build_copy_short,
    humanize_stat_key,
    parse_range,
)


def format_number(value: float) -> str:
    if math.isclose(value, round(value), rel_tol=1e-9, abs_tol=1e-9):
        return f"{int(round(value)):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


CONSTRAINT_OPERATORS = (">=", "<=", "=", ">", "<")
ROLL_MODE_OPTIONS = {
    "Worst Case": "worst",
    "Average": "average",
    "Best Case": "best",
}
ROLL_MODE_LABELS = {value: label for label, value in ROLL_MODE_OPTIONS.items()}


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str


@dataclass(frozen=True)
class ObjectiveTerm:
    metric_key: str
    weight: float = 1.0


@dataclass(frozen=True)
class OptimizationObjective:
    terms: tuple[ObjectiveTerm, ...]
    scales: tuple[float, ...] = tuple()

    def is_single_metric(self) -> bool:
        return len(self.terms) == 1

    def primary_metric_key(self) -> str:
        if not self.terms:
            return "hp"
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
        return OptimizationObjective(
            terms=self.terms,
            scales=tuple(max(1.0, abs(float(scale))) for scale in scales),
        )


@dataclass(frozen=True)
class OptimizationConstraint:
    metric_key: str
    operator: str
    target: float

    def display_label(self) -> str:
        return f"{METRIC_DEFINITIONS[self.metric_key].label} {self.operator} {format_number(self.target)}"


@dataclass(frozen=True)
class CraftSearchOption:
    result: CraftResult
    objective_label: str
    objective_value: float
    objective: OptimizationObjective
    roll_mode: str
    constraint_values: dict[str, float]

    @property
    def selection_values(self) -> tuple[str, ...]:
        return self.result.selection.ingredient_names


@dataclass(frozen=True)
class IngredientCandidate:
    ingredient_name: str
    metric_values: dict[str, float]
    objective_value: float
    scaled_objective_value: float
    utility: float
    interaction_score: float
    positive_interaction_score: float
    direct_effect_score: float


@dataclass(frozen=True)
class PreparedCraftSearch:
    base_result: CraftResult
    objective: OptimizationObjective
    constraints: tuple[OptimizationConstraint, ...]
    roll_mode: str
    open_slots: tuple[int, ...]
    slot_order: tuple[int, ...]
    candidate_names_by_slot: dict[int, tuple[str, ...]]
    total_states: int


@dataclass
class CraftMCTSNode:
    depth: int
    assignments: tuple[str, ...]
    parent: "CraftMCTSNode | None"
    untried_candidates: list[str]
    children: list["CraftMCTSNode"] = field(default_factory=list)
    visits: int = 0
    total_reward: float = 0.0
    best_reward: float = float("-inf")
    fully_explored: bool = False


@dataclass(frozen=True)
class ExactIngredientOption:
    ingredient_name: str
    metric_values: tuple[float, ...]
    objective_value: float


@dataclass
class ExactCandidateSet:
    ingredient_names: tuple[str, ...]
    objective_max_table: "RangeQueryTable"
    metric_max_tables: tuple["RangeQueryTable", ...]
    metric_min_tables: tuple["RangeQueryTable", ...]
    options_by_effect: dict[int, tuple[ExactIngredientOption, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ExactSearchContext:
    prepared: PreparedCraftSearch
    metric_keys: tuple[str, ...]
    metric_index: dict[str, int]
    constraint_metric_indices: tuple[int, ...]
    objective_coefficients: tuple[float, ...]
    base_metric_values: tuple[float, ...]
    base_objective_value: float
    open_slots: tuple[int, ...]
    open_slot_set: frozenset[int]
    open_slot_order: tuple[int, ...]
    fixed_ingredient_names: tuple[str, ...]
    fixed_effect_delta: tuple[int, ...]
    remaining_effect_bounds_by_depth: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]
    available_patterns: tuple[tuple[tuple[str, int], ...], ...]
    delta_by_slot_pattern: dict[int, dict[tuple[tuple[str, int], ...], tuple[int, ...]]]
    effect_min: int
    effect_max: int
    any_candidate_set: ExactCandidateSet | None
    candidate_sets_by_pattern: dict[tuple[tuple[str, int], ...], ExactCandidateSet]
    fixed_candidate_sets_by_slot: dict[int, ExactCandidateSet]
    metric_cache: dict[tuple[str, int], tuple[float, ...]]


class RangeQueryTable:
    def __init__(self, values: list[float], use_max: bool) -> None:
        self._values = values
        self._use_max = use_max
        self._logs = [0] * (len(values) + 1)
        for index in range(2, len(values) + 1):
            self._logs[index] = self._logs[index // 2] + 1

        comparator = max if use_max else min
        self._table: list[list[float]] = [values[:]]
        level = 1
        while (1 << level) <= len(values):
            span = 1 << level
            half = span >> 1
            previous = self._table[level - 1]
            row = [
                comparator(previous[index], previous[index + half])
                for index in range(len(values) - span + 1)
            ]
            self._table.append(row)
            level += 1

    def query(self, start_index: int, end_index: int) -> float:
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        length = (end_index - start_index) + 1
        level = self._logs[length]
        span = 1 << level
        left = self._table[level][start_index]
        right = self._table[level][end_index - span + 1]
        return max(left, right) if self._use_max else min(left, right)


def build_metric_definitions() -> dict[str, MetricDefinition]:
    definitions: dict[str, MetricDefinition] = {
        "weapon_damage_avg": MetricDefinition("weapon_damage_avg", "Weapon Damage Avg"),
    }
    direct_keys = [
        "hp",
        "durability",
        "duration",
        "charges",
        "slots",
        "strReq",
        "dexReq",
        "intReq",
        "defReq",
        "agiReq",
        "eDef",
        "tDef",
        "wDef",
        "fDef",
        "aDef",
    ]
    for key in direct_keys:
        definitions[key] = MetricDefinition(key, humanize_stat_key(key))
    for key in SKP_ORDER:
        definitions[key] = MetricDefinition(key, humanize_stat_key(key))
    for key in ROLLED_IDS:
        definitions[key] = MetricDefinition(key, humanize_stat_key(key))
    return definitions


METRIC_DEFINITIONS = build_metric_definitions()
METRIC_LABEL_TO_KEY = {definition.label.lower(): key for key, definition in METRIC_DEFINITIONS.items()}
METRIC_DISPLAY_OPTIONS = sorted({definition.label for definition in METRIC_DEFINITIONS.values()}, key=str.casefold)


def resolve_metric_key(raw_text: str) -> str | None:
    normalized = raw_text.strip().lower()
    if not normalized:
        return None
    if normalized in METRIC_LABEL_TO_KEY:
        return METRIC_LABEL_TO_KEY[normalized]
    for key in METRIC_DEFINITIONS:
        if key.lower() == normalized:
            return key
    return None


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
        ordered_keys = ["hp"]
        merged = {"hp": 1.0}

    return OptimizationObjective(
        terms=tuple(
            ObjectiveTerm(metric_key=metric_key, weight=merged[metric_key])
            for metric_key in ordered_keys
        ),
    )


def coerce_optimization_objective(
    raw_objective: str | OptimizationObjective | None,
) -> OptimizationObjective:
    if isinstance(raw_objective, OptimizationObjective):
        if raw_objective.terms:
            return raw_objective
        return make_optimization_objective((("hp", 1.0),))
    if isinstance(raw_objective, str):
        metric_key = raw_objective if raw_objective in METRIC_DEFINITIONS else "hp"
        return make_optimization_objective(((metric_key, 1.0),))
    return make_optimization_objective((("hp", 1.0),))


class CrafterOptimizer:
    EXACT_MAX_STATES = 120_000
    EXACT_MIN_SLOT_CANDIDATES = 5
    MCTS_SLOT_CAP = 18
    MCTS_MAX_ITERATIONS = 20_000
    PRIMARY_SLOT_KEEP = 10
    POSITIONAL_SEED_KEEP = 6
    TERM_SLOT_KEEP = 6
    CONSTRAINT_SLOT_KEEP = 6
    INTERACTION_SLOT_KEEP = 4
    EXACT_OBJECTIVE_PROTECT_BUDGET = 4
    EXACT_CONSTRAINT_PROTECT = 2
    PROGRESS_INTERVAL_SECONDS = 0.6

    def __init__(self, data: CrafterData) -> None:
        self.data = data
        self._valid_ingredient_cache: dict[tuple[str, int], tuple[str, ...]] = {}
        self._random = random.Random()

    def metric_value_from_result(
        self,
        result: CraftResult,
        metric_key: str,
        roll_mode: str = "average",
    ) -> float:
        stat_map = result.stat_map
        if metric_key == "weapon_damage_avg":
            return self._weapon_damage_avg(result, roll_mode)
        if metric_key in SKP_ORDER or metric_key in ROLLED_IDS:
            low_value = float(stat_map["minRolls"].get(metric_key, 0))
            high_value = float(stat_map["maxRolls"].get(metric_key, 0))
            return self._pick_roll_value(low_value, high_value, roll_mode)
        if metric_key == "durability":
            return self._pick_pair_value(stat_map.get("durability", (0, 0)), roll_mode)
        if metric_key == "duration":
            return self._pick_pair_value(stat_map.get("duration", (0, 0)), roll_mode)
        if metric_key == "hp":
            return self._hp_metric_value(result, roll_mode)
        return float(stat_map.get(metric_key, 0.0) or 0.0)

    def objective_value_from_result(
        self,
        result: CraftResult,
        objective: str | OptimizationObjective,
        roll_mode: str = "average",
    ) -> float:
        objective_spec = coerce_optimization_objective(objective)
        metric_values = {
            term.metric_key: self.metric_value_from_result(result, term.metric_key, roll_mode)
            for term in objective_spec.terms
        }
        return self._objective_value_from_metric_values(metric_values, objective_spec, scaled=False)

    def objective_breakdown_from_result(
        self,
        result: CraftResult,
        objective: str | OptimizationObjective,
        roll_mode: str = "average",
    ) -> list[tuple[str, float, float, float]]:
        objective_spec = coerce_optimization_objective(objective)
        metric_values = {
            term.metric_key: self.metric_value_from_result(result, term.metric_key, roll_mode)
            for term in objective_spec.terms
        }
        breakdown: list[tuple[str, float, float, float]] = []
        for index, term in enumerate(objective_spec.terms):
            raw_value = metric_values.get(term.metric_key, 0.0)
            if objective_spec.is_single_metric():
                contribution = raw_value
            else:
                contribution = (
                    objective_spec.normalized_weight(index)
                    * (raw_value / objective_spec.scale_for_index(index, raw_value))
                )
            breakdown.append(
                (
                    METRIC_DEFINITIONS[term.metric_key].label,
                    term.weight,
                    raw_value,
                    contribution,
                )
            )
        return breakdown

    def prepare_search(
        self,
        base_selection: CraftSelection,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        roll_mode: str,
        mode: str,
    ) -> PreparedCraftSearch:
        base_result = self.data.craft(base_selection)
        if base_result.warnings:
            raise ValueError(
                "Current selected ingredients produce warnings. Clear or replace them before searching."
            )

        objective = coerce_optimization_objective(objective_metric)
        roll_mode = self._normalize_roll_mode(roll_mode)
        open_slots = tuple(
            idx
            for idx, ingredient_name in enumerate(base_result.selection.ingredient_names)
            if ingredient_name == "No Ingredient"
        )
        if not open_slots:
            calibrated = self._calibrate_objective(objective, [base_result], roll_mode)
            return PreparedCraftSearch(
                base_result=base_result,
                objective=calibrated,
                constraints=tuple(constraints),
                roll_mode=roll_mode,
                open_slots=open_slots,
                slot_order=tuple(),
                candidate_names_by_slot={},
                total_states=1,
            )

        candidate_metrics = {term.metric_key for term in objective.terms}
        candidate_metrics.update(constraint.metric_key for constraint in constraints)
        valid_ingredient_names = self._valid_ingredient_names_for_recipe(base_result.recipe)

        sampled_results: list[CraftResult] = [base_result]
        raw_candidates_by_slot: dict[int, list[IngredientCandidate]] = {}
        for slot_index in open_slots:
            slot_candidates: list[IngredientCandidate] = []
            for ingredient_name in valid_ingredient_names:
                trial_result = self._result_with_replacement(base_result.selection, slot_index, ingredient_name)
                if trial_result.warnings:
                    continue
                metric_values = {
                    metric_key: self.metric_value_from_result(trial_result, metric_key, roll_mode)
                    for metric_key in candidate_metrics
                }
                ingredient = self.data.ingredients_by_name[ingredient_name]
                interaction_score = float(sum(abs(value) for value in ingredient.pos_mods.values()))
                positive_interaction_score = float(sum(max(0, value) for value in ingredient.pos_mods.values()))
                direct_effect_score = float(
                    sum(abs(value) for value in ingredient.item_ids.values())
                    + sum(abs(value) for value in ingredient.consumable_ids.values())
                    + sum(abs(value) for value in ingredient.min_rolls.values())
                    + sum(abs(value) for value in ingredient.max_rolls.values())
                )
                slot_candidates.append(
                    IngredientCandidate(
                        ingredient_name=ingredient_name,
                        metric_values=metric_values,
                        objective_value=0.0,
                        scaled_objective_value=0.0,
                        utility=0.0,
                        interaction_score=interaction_score,
                        positive_interaction_score=positive_interaction_score,
                        direct_effect_score=direct_effect_score,
                    )
                )
                sampled_results.append(trial_result)
            raw_candidates_by_slot[slot_index] = slot_candidates

        calibrated_objective = self._calibrate_objective(objective, sampled_results, roll_mode)
        candidate_names_by_slot: dict[int, tuple[str, ...]] = {}
        exact_protected_names_by_slot: dict[int, set[str]] = {}
        for slot_index in open_slots:
            candidates: list[IngredientCandidate] = []
            for candidate in raw_candidates_by_slot[slot_index]:
                objective_value = self._objective_value_from_metric_values(
                    candidate.metric_values,
                    calibrated_objective,
                    scaled=False,
                )
                scaled_objective_value = self._objective_value_from_metric_values(
                    candidate.metric_values,
                    calibrated_objective,
                    scaled=True,
                )
                penalty = self._constraint_penalty_sum(candidate.metric_values, constraints)
                candidates.append(
                    IngredientCandidate(
                        ingredient_name=candidate.ingredient_name,
                        metric_values=candidate.metric_values,
                        objective_value=objective_value,
                        scaled_objective_value=scaled_objective_value,
                        utility=scaled_objective_value - (penalty * 3.0),
                        interaction_score=candidate.interaction_score,
                        positive_interaction_score=candidate.positive_interaction_score,
                        direct_effect_score=candidate.direct_effect_score,
                    )
                )

            ordered_candidates = self._select_slot_candidates(
                candidates,
                calibrated_objective,
                constraints,
                self.MCTS_SLOT_CAP,
            )
            if mode == "exact":
                exact_protected_names_by_slot[slot_index] = self._select_exact_protected_names(
                    ordered_candidates,
                    calibrated_objective,
                    constraints,
                )
            candidate_names_by_slot[slot_index] = tuple(
                candidate.ingredient_name for candidate in ordered_candidates
            )

        if mode == "exact":
            candidate_names_by_slot = self._trim_exact_candidate_pool(
                candidate_names_by_slot,
                exact_protected_names_by_slot,
            )

        slot_order = tuple(sorted(open_slots, key=lambda slot: (len(candidate_names_by_slot[slot]), slot)))
        total_states = 1
        for slot_index in open_slots:
            total_states *= max(1, len(candidate_names_by_slot[slot_index]))

        return PreparedCraftSearch(
            base_result=base_result,
            objective=calibrated_objective,
            constraints=tuple(constraints),
            roll_mode=roll_mode,
            open_slots=open_slots,
            slot_order=slot_order,
            candidate_names_by_slot=candidate_names_by_slot,
            total_states=total_states,
        )

    def generate(
        self,
        base_selection: CraftSelection,
        objective_metric: str | OptimizationObjective,
        constraints: list[OptimizationConstraint],
        roll_mode: str,
        mode: str,
        top_n: int,
        stop_event: threading.Event | None = None,
        progress_callback: Callable[[list[CraftSearchOption], int, int, float, str], None] | None = None,
    ) -> list[CraftSearchOption]:
        if mode == "mcts":
            prepared = self.prepare_search(base_selection, objective_metric, constraints, roll_mode, mode)
            return self._generate_mcts(prepared, top_n, stop_event, progress_callback)
        prepared = self.prepare_search(base_selection, objective_metric, constraints, roll_mode, "mcts")
        if self._supports_true_exact(prepared):
            return self._generate_exact_true(prepared, top_n, stop_event, progress_callback)
        filtered_prepared = self.prepare_search(base_selection, objective_metric, constraints, roll_mode, mode)
        return self._generate_exact(filtered_prepared, top_n, stop_event, progress_callback)

    def _supports_true_exact(
        self,
        prepared: PreparedCraftSearch,
    ) -> bool:
        metric_keys = {term.metric_key for term in prepared.objective.terms}
        metric_keys.update(constraint.metric_key for constraint in prepared.constraints)
        if "weapon_damage_avg" in metric_keys:
            return False
        if any(term.metric_key in {"durability", "duration"} for term in prepared.objective.terms):
            return False
        if prepared.base_result.recipe.type_key in CONSUMABLE_TYPES:
            return False
        return True

    @staticmethod
    def _pattern_signature(ingredient: Ingredient) -> tuple[tuple[str, int], ...]:
        return tuple(sorted((key, value) for key, value in ingredient.pos_mods.items() if value))

    @staticmethod
    def _dot_product(left: Iterable[float], right: Iterable[float]) -> float:
        return sum(left_value * right_value for left_value, right_value in zip(left, right))

    def _metric_tuple_for_ingredient_effect(
        self,
        context: ExactSearchContext,
        ingredient_name: str,
        effect: int,
    ) -> tuple[float, ...]:
        cache_key = (ingredient_name, effect)
        cached = context.metric_cache.get(cache_key)
        if cached is not None:
            return cached
        ingredient = self.data.ingredients_by_name[ingredient_name]
        metric_values = tuple(
            self._metric_value_for_ingredient_effect(
                context.prepared.base_result.recipe,
                ingredient,
                metric_key,
                effect,
                context.prepared.roll_mode,
            )
            for metric_key in context.metric_keys
        )
        context.metric_cache[cache_key] = metric_values
        return metric_values

    def _metric_value_for_ingredient_effect(
        self,
        recipe: Recipe,
        ingredient: Ingredient,
        metric_key: str,
        effect: int,
        roll_mode: str,
    ) -> float:
        effect_multiplier = float(f"{effect / 100:.2f}")
        if metric_key in SKP_ORDER or metric_key in ROLLED_IDS:
            low_value = math.floor(ingredient.min_rolls.get(metric_key, 0) * effect_multiplier)
            high_value = math.floor(ingredient.max_rolls.get(metric_key, 0) * effect_multiplier)
            rolled_low, rolled_high = sorted((low_value, high_value))
            return self._pick_roll_value(float(rolled_low), float(rolled_high), roll_mode)
        if metric_key == "durability":
            return float(ingredient.item_ids.get("dura", 0.0))
        if metric_key == "duration":
            return float(ingredient.consumable_ids.get("dura", 0.0))
        if metric_key == "charges":
            return float(ingredient.consumable_ids.get("charges", 0.0))
        if metric_key == "slots":
            return 0.0
        if metric_key == "hp":
            return 0.0

        value = 0.0
        if (
            ingredient.is_powder
            and ingredient.pid is not None
            and recipe.type_key in ARMOR_TYPES.union(ACCESSORY_TYPES)
        ):
            powder = POWDER_STATS[ingredient.pid]
            element = SKP_ELEMENTS[ingredient.pid // 6]
            previous = SKP_ELEMENTS[(SKP_ELEMENTS.index(element) + 4) % 5]
            if metric_key == f"{element}Def":
                value += float(powder.def_plus)
            if metric_key == f"{previous}Def":
                value -= float(powder.def_minus)

        direct_value = float(ingredient.item_ids.get(metric_key, 0.0))
        if direct_value:
            if ingredient.is_powder:
                value += direct_value
            else:
                value += float(round(direct_value * effect_multiplier))
        return value

    def _build_exact_candidate_set(
        self,
        context: ExactSearchContext,
        ingredient_names: tuple[str, ...],
    ) -> ExactCandidateSet:
        effect_values = list(range(context.effect_min, context.effect_max + 1))
        objective_values: list[float] = []
        metric_max_values = [
            [float("-inf")] * len(effect_values)
            for _ in context.metric_keys
        ]
        metric_min_values = [
            [float("inf")] * len(effect_values)
            for _ in context.metric_keys
        ]

        for effect_offset, effect in enumerate(effect_values):
            best_objective = float("-inf")
            for ingredient_name in ingredient_names:
                metric_values = self._metric_tuple_for_ingredient_effect(context, ingredient_name, effect)
                objective_value = self._dot_product(context.objective_coefficients, metric_values)
                best_objective = max(best_objective, objective_value)
                for metric_index, metric_value in enumerate(metric_values):
                    metric_max_values[metric_index][effect_offset] = max(
                        metric_max_values[metric_index][effect_offset],
                        metric_value,
                    )
                    metric_min_values[metric_index][effect_offset] = min(
                        metric_min_values[metric_index][effect_offset],
                        metric_value,
                    )
            objective_values.append(best_objective)

        return ExactCandidateSet(
            ingredient_names=ingredient_names,
            objective_max_table=RangeQueryTable(objective_values, use_max=True),
            metric_max_tables=tuple(
                RangeQueryTable(metric_values, use_max=True)
                for metric_values in metric_max_values
            ),
            metric_min_tables=tuple(
                RangeQueryTable(metric_values, use_max=False)
                for metric_values in metric_min_values
            ),
        )

    @staticmethod
    def _exact_constraint_feasibility_bounds(
        constraint: OptimizationConstraint,
        minimum_value: float,
        maximum_value: float,
    ) -> tuple[float, float]:
        if constraint.metric_key in {"durability", "duration"}:
            return minimum_value - 1.0, maximum_value
        return minimum_value, maximum_value

    @staticmethod
    def _delta_vector_for_slot_pattern(
        slot_index: int,
        pattern_signature: tuple[tuple[str, int], ...],
    ) -> tuple[int, ...]:
        row = slot_index // 2
        col = slot_index % 2
        pos_mods = dict(pattern_signature)
        deltas = [0] * 6
        for target_index in range(6):
            target_row = target_index // 2
            target_col = target_index % 2
            delta = 0
            if target_col == col:
                if target_row < row:
                    delta += pos_mods.get("above", 0)
                elif target_row > row:
                    delta += pos_mods.get("under", 0)
            if row == target_row:
                if col == 1 and target_col == 0:
                    delta += pos_mods.get("left", 0)
                elif col == 0 and target_col == 1:
                    delta += pos_mods.get("right", 0)
            if (abs(target_row - row) == 1 and abs(target_col - col) == 0) or (
                abs(target_row - row) == 0 and abs(target_col - col) == 1
            ):
                delta += pos_mods.get("touching", 0)
            if abs(target_row - row) > 1 or (
                abs(target_row - row) == 1 and abs(target_col - col) == 1
            ):
                delta += pos_mods.get("notTouching", 0)
            deltas[target_index] = delta
        return tuple(deltas)

    def _build_exact_search_context(self, prepared: PreparedCraftSearch) -> ExactSearchContext:
        metric_keys: list[str] = []
        for term in prepared.objective.terms:
            if term.metric_key not in metric_keys:
                metric_keys.append(term.metric_key)
        for constraint in prepared.constraints:
            if constraint.metric_key not in metric_keys:
                metric_keys.append(constraint.metric_key)
        metric_index = {metric_key: index for index, metric_key in enumerate(metric_keys)}
        constraint_metric_indices = tuple(metric_index[constraint.metric_key] for constraint in prepared.constraints)

        objective_coefficients = [0.0] * len(metric_keys)
        if prepared.objective.is_single_metric():
            objective_coefficients[metric_index[prepared.objective.primary_metric_key()]] = 1.0
        else:
            for objective_index, term in enumerate(prepared.objective.terms):
                coefficient = (
                    prepared.objective.normalized_weight(objective_index)
                    / prepared.objective.scale_for_index(objective_index)
                )
                objective_coefficients[metric_index[term.metric_key]] += coefficient

        valid_ingredient_names = self._valid_ingredient_names_for_recipe(prepared.base_result.recipe)
        ingredient_names_by_pattern: dict[tuple[tuple[str, int], ...], list[str]] = {}
        for ingredient_name in valid_ingredient_names:
            signature = self._pattern_signature(self.data.ingredients_by_name[ingredient_name])
            ingredient_names_by_pattern.setdefault(signature, []).append(ingredient_name)
        available_patterns = tuple(
            sorted(
                ingredient_names_by_pattern,
                key=lambda signature: (
                    len(ingredient_names_by_pattern[signature]),
                    len(signature),
                    str(signature),
                ),
            )
        )

        delta_by_slot_pattern = {
            slot_index: {
                pattern_signature: self._delta_vector_for_slot_pattern(slot_index, pattern_signature)
                for pattern_signature in available_patterns
            }
            for slot_index in range(6)
        }

        fixed_effect_delta = [0] * 6
        fixed_ingredient_names = prepared.base_result.selection.ingredient_names
        open_slot_set = frozenset(prepared.open_slots)
        for slot_index, ingredient_name in enumerate(fixed_ingredient_names):
            if slot_index in open_slot_set or ingredient_name == "No Ingredient":
                continue
            ingredient = self.data.ingredients_by_name[ingredient_name]
            delta_vector = delta_by_slot_pattern[slot_index][self._pattern_signature(ingredient)]
            for target_index, value in enumerate(delta_vector):
                fixed_effect_delta[target_index] += value

        slot_extrema_min: dict[int, tuple[int, ...]] = {}
        slot_extrema_max: dict[int, tuple[int, ...]] = {}
        slot_influence: dict[int, int] = {}
        for slot_index in prepared.open_slots:
            min_values = []
            max_values = []
            influence = 0
            for target_index in range(6):
                deltas = [
                    delta_by_slot_pattern[slot_index][pattern_signature][target_index]
                    for pattern_signature in available_patterns
                ]
                min_values.append(min(deltas))
                max_values.append(max(deltas))
                influence += max(abs(value) for value in deltas)
            slot_extrema_min[slot_index] = tuple(min_values)
            slot_extrema_max[slot_index] = tuple(max_values)
            slot_influence[slot_index] = influence

        open_slot_order = tuple(
            sorted(
                prepared.open_slots,
                key=lambda slot_index: (-slot_influence[slot_index], slot_index),
            )
        )

        suffix_min = [[0] * 6 for _ in range(len(open_slot_order) + 1)]
        suffix_max = [[0] * 6 for _ in range(len(open_slot_order) + 1)]
        for depth in range(len(open_slot_order) - 1, -1, -1):
            slot_index = open_slot_order[depth]
            for target_index in range(6):
                suffix_min[depth][target_index] = (
                    suffix_min[depth + 1][target_index] + slot_extrema_min[slot_index][target_index]
                )
                suffix_max[depth][target_index] = (
                    suffix_max[depth + 1][target_index] + slot_extrema_max[slot_index][target_index]
                )

        effect_min = min(
            100 + fixed_effect_delta[target_index] + suffix_min[0][target_index]
            for target_index in range(6)
        )
        effect_max = max(
            100 + fixed_effect_delta[target_index] + suffix_max[0][target_index]
            for target_index in range(6)
        )

        empty_selection = CraftSelection(
            recipe_name=prepared.base_result.selection.recipe_name,
            level_range=prepared.base_result.selection.level_range,
            mat_tiers=prepared.base_result.selection.mat_tiers,
            ingredient_names=("No Ingredient",) * 6,
            attack_speed=prepared.base_result.selection.attack_speed,
        )
        empty_result = self.data.craft(empty_selection)
        base_metric_values = tuple(
            self.metric_value_from_result(empty_result, metric_key, prepared.roll_mode)
            for metric_key in metric_keys
        )
        metric_cache: dict[tuple[str, int], tuple[float, ...]] = {}

        provisional_context = ExactSearchContext(
            prepared=prepared,
            metric_keys=tuple(metric_keys),
            metric_index=metric_index,
            constraint_metric_indices=constraint_metric_indices,
            objective_coefficients=tuple(objective_coefficients),
            base_metric_values=base_metric_values,
            base_objective_value=self._dot_product(objective_coefficients, base_metric_values),
            open_slots=prepared.open_slots,
            open_slot_set=open_slot_set,
            open_slot_order=open_slot_order,
            fixed_ingredient_names=fixed_ingredient_names,
            fixed_effect_delta=tuple(fixed_effect_delta),
            remaining_effect_bounds_by_depth=tuple(
                (tuple(suffix_min[depth]), tuple(suffix_max[depth]))
                for depth in range(len(open_slot_order) + 1)
            ),
            available_patterns=available_patterns,
            delta_by_slot_pattern=delta_by_slot_pattern,
            effect_min=effect_min,
            effect_max=effect_max,
            any_candidate_set=None,
            candidate_sets_by_pattern={},
            fixed_candidate_sets_by_slot={},
            metric_cache=metric_cache,
        )

        candidate_sets_by_pattern = {
            pattern_signature: self._build_exact_candidate_set(
                provisional_context,
                tuple(ingredient_names),
            )
            for pattern_signature, ingredient_names in ingredient_names_by_pattern.items()
        }
        any_candidate_set = self._build_exact_candidate_set(
            provisional_context,
            tuple(valid_ingredient_names),
        )
        fixed_candidate_sets_by_slot = {
            slot_index: self._build_exact_candidate_set(
                provisional_context,
                (ingredient_name,),
            )
            for slot_index, ingredient_name in enumerate(fixed_ingredient_names)
            if slot_index not in open_slot_set
        }

        return ExactSearchContext(
            prepared=provisional_context.prepared,
            metric_keys=provisional_context.metric_keys,
            metric_index=provisional_context.metric_index,
            constraint_metric_indices=provisional_context.constraint_metric_indices,
            objective_coefficients=provisional_context.objective_coefficients,
            base_metric_values=provisional_context.base_metric_values,
            base_objective_value=provisional_context.base_objective_value,
            open_slots=provisional_context.open_slots,
            open_slot_set=provisional_context.open_slot_set,
            open_slot_order=provisional_context.open_slot_order,
            fixed_ingredient_names=provisional_context.fixed_ingredient_names,
            fixed_effect_delta=provisional_context.fixed_effect_delta,
            remaining_effect_bounds_by_depth=provisional_context.remaining_effect_bounds_by_depth,
            available_patterns=provisional_context.available_patterns,
            delta_by_slot_pattern=provisional_context.delta_by_slot_pattern,
            effect_min=provisional_context.effect_min,
            effect_max=provisional_context.effect_max,
            any_candidate_set=any_candidate_set,
            candidate_sets_by_pattern=candidate_sets_by_pattern,
            fixed_candidate_sets_by_slot=fixed_candidate_sets_by_slot,
            metric_cache=provisional_context.metric_cache,
        )

    def _exact_candidate_set_range_value(
        self,
        context: ExactSearchContext,
        candidate_set: ExactCandidateSet,
        table: RangeQueryTable,
        effect_low: int,
        effect_high: int,
    ) -> float:
        start_index = max(context.effect_min, min(effect_low, effect_high)) - context.effect_min
        end_index = min(context.effect_max, max(effect_low, effect_high)) - context.effect_min
        return table.query(start_index, end_index)

    def _exact_options_for_candidate_set(
        self,
        context: ExactSearchContext,
        candidate_set: ExactCandidateSet,
        effect: int,
    ) -> tuple[ExactIngredientOption, ...]:
        cached = candidate_set.options_by_effect.get(effect)
        if cached is not None:
            return cached

        options = [
            ExactIngredientOption(
                ingredient_name=ingredient_name,
                metric_values=self._metric_tuple_for_ingredient_effect(context, ingredient_name, effect),
                objective_value=self._dot_product(
                    context.objective_coefficients,
                    self._metric_tuple_for_ingredient_effect(context, ingredient_name, effect),
                ),
            )
            for ingredient_name in candidate_set.ingredient_names
        ]
        pruned = self._prune_exact_slot_candidates(
            options,
            context.prepared.constraints,
            context.metric_index,
        )
        candidate_set.options_by_effect[effect] = tuple(pruned)
        return candidate_set.options_by_effect[effect]

    def _prune_exact_slot_candidates(
        self,
        options: list[ExactIngredientOption],
        constraints: tuple[OptimizationConstraint, ...],
        metric_index: dict[str, int],
    ) -> list[ExactIngredientOption]:
        if any(constraint.metric_key in {"durability", "duration"} for constraint in constraints):
            return sorted(
                options,
                key=lambda option: (option.objective_value, option.ingredient_name != "No Ingredient"),
                reverse=True,
            )
        ordered = sorted(
            options,
            key=lambda option: (option.objective_value, option.ingredient_name != "No Ingredient"),
            reverse=True,
        )
        kept: list[ExactIngredientOption] = []
        for option in ordered:
            if any(
                self._exact_candidate_dominates(existing, option, constraints, metric_index)
                for existing in kept
            ):
                continue
            kept = [
                existing
                for existing in kept
                if not self._exact_candidate_dominates(option, existing, constraints, metric_index)
            ]
            kept.append(option)
        kept.sort(
            key=lambda option: (option.objective_value, option.ingredient_name != "No Ingredient"),
            reverse=True,
        )
        return kept

    @staticmethod
    def _exact_candidate_dominates(
        left: ExactIngredientOption,
        right: ExactIngredientOption,
        constraints: tuple[OptimizationConstraint, ...],
        metric_index: dict[str, int],
    ) -> bool:
        if left.objective_value < right.objective_value - 1e-9:
            return False
        strictly_better = left.objective_value > right.objective_value + 1e-9
        for constraint in constraints:
            if constraint.metric_key in {"durability", "duration"}:
                continue
            metric_pos = metric_index[constraint.metric_key]
            left_value = left.metric_values[metric_pos]
            right_value = right.metric_values[metric_pos]
            if constraint.operator in {">=", ">"}:
                if left_value < right_value - 1e-9:
                    return False
                strictly_better = strictly_better or left_value > right_value + 1e-9
            elif constraint.operator in {"<=", "<"}:
                if left_value > right_value + 1e-9:
                    return False
                strictly_better = strictly_better or left_value < right_value - 1e-9
            else:
                if not math.isclose(left_value, right_value, rel_tol=1e-9, abs_tol=1e-9):
                    return False
        return strictly_better

    def _generate_exact_true(
        self,
        prepared: PreparedCraftSearch,
        top_n: int,
        stop_event: threading.Event | None,
        progress_callback: Callable[[list[CraftSearchOption], int, int, float, str], None] | None,
    ) -> list[CraftSearchOption]:
        started = time.perf_counter()
        next_progress = started + self.PROGRESS_INTERVAL_SECONDS
        if not prepared.open_slots:
            single = self._build_option_from_selection(
                prepared.base_result.selection,
                prepared.objective,
                prepared.constraints,
                prepared.roll_mode,
            )
            return [single] if single is not None else []

        context = self._build_exact_search_context(prepared)
        ranked_options: list[CraftSearchOption] = []
        option_signatures: set[tuple[str, ...]] = set()
        explored_layouts = 0
        total_layouts = max(1, len(context.available_patterns) ** len(context.open_slots))
        assigned_patterns: dict[int, tuple[tuple[str, int], ...]] = {}
        current_effect_delta = list(context.fixed_effect_delta)

        def push_option(option: CraftSearchOption) -> None:
            if option.selection_values in option_signatures:
                return
            option_signatures.add(option.selection_values)
            ranked_options.append(option)
            ranked_options.sort(key=lambda value: value.objective_value, reverse=True)
            if len(ranked_options) > top_n:
                removed = ranked_options.pop()
                option_signatures.discard(removed.selection_values)

        def current_threshold() -> float:
            if len(ranked_options) < top_n:
                return float("-inf")
            return ranked_options[-1].objective_value

        def maybe_emit_progress(detail: str) -> None:
            nonlocal next_progress
            if progress_callback is None:
                return
            now = time.perf_counter()
            if now < next_progress:
                return
            next_progress = now + self.PROGRESS_INTERVAL_SECONDS
            progress_callback(
                list(ranked_options),
                explored_layouts,
                total_layouts,
                now - started,
                detail,
            )

        def branch_upper_bound(depth: int) -> float | None:
            remaining_min, remaining_max = context.remaining_effect_bounds_by_depth[depth]
            objective_upper = context.base_objective_value
            constraint_mins = [context.base_metric_values[index] for index in context.constraint_metric_indices]
            constraint_maxes = [context.base_metric_values[index] for index in context.constraint_metric_indices]

            for slot_index in range(6):
                effect_low = 100 + current_effect_delta[slot_index] + remaining_min[slot_index]
                effect_high = 100 + current_effect_delta[slot_index] + remaining_max[slot_index]
                if slot_index in context.open_slot_set:
                    pattern_signature = assigned_patterns.get(slot_index)
                    candidate_set = (
                        context.any_candidate_set
                        if pattern_signature is None
                        else context.candidate_sets_by_pattern[pattern_signature]
                    )
                else:
                    candidate_set = context.fixed_candidate_sets_by_slot[slot_index]

                objective_upper += self._exact_candidate_set_range_value(
                    context,
                    candidate_set,
                    candidate_set.objective_max_table,
                    effect_low,
                    effect_high,
                )
                for constraint_index, constraint in enumerate(context.prepared.constraints):
                    metric_pos = context.constraint_metric_indices[constraint_index]
                    constraint_mins[constraint_index] += self._exact_candidate_set_range_value(
                        context,
                        candidate_set,
                        candidate_set.metric_min_tables[metric_pos],
                        effect_low,
                        effect_high,
                    )
                    constraint_maxes[constraint_index] += self._exact_candidate_set_range_value(
                        context,
                        candidate_set,
                        candidate_set.metric_max_tables[metric_pos],
                        effect_low,
                        effect_high,
                    )

            for constraint_index, constraint in enumerate(context.prepared.constraints):
                feasible_min, feasible_max = self._exact_constraint_feasibility_bounds(
                    constraint,
                    constraint_mins[constraint_index],
                    constraint_maxes[constraint_index],
                )
                if constraint.operator in {">=", ">"} and feasible_max < constraint.target:
                    return None
                if constraint.operator in {"<=", "<"} and feasible_min > constraint.target:
                    return None
                if constraint.operator == "=" and not (
                    feasible_min <= constraint.target <= feasible_max
                ):
                    return None
            return objective_upper

        def search_leaf() -> None:
            ingredient_names = list(context.fixed_ingredient_names)
            metric_totals = list(context.base_metric_values)
            for slot_index in range(6):
                effect = 100 + current_effect_delta[slot_index]
                if slot_index in context.open_slot_set:
                    continue
                fixed_option = self._exact_options_for_candidate_set(
                    context,
                    context.fixed_candidate_sets_by_slot[slot_index],
                    effect,
                )[0]
                ingredient_names[slot_index] = fixed_option.ingredient_name
                for metric_pos, metric_value in enumerate(fixed_option.metric_values):
                    metric_totals[metric_pos] += metric_value

            slot_candidates: list[tuple[int, tuple[ExactIngredientOption, ...]]] = []
            for slot_index in context.open_slots:
                effect = 100 + current_effect_delta[slot_index]
                pattern_signature = assigned_patterns[slot_index]
                candidate_set = context.candidate_sets_by_pattern[pattern_signature]
                slot_candidates.append(
                    (
                        slot_index,
                        self._exact_options_for_candidate_set(context, candidate_set, effect),
                    )
                )
            slot_candidates.sort(key=lambda entry: (len(entry[1]), entry[0]))

            suffix_objective = [0.0] * (len(slot_candidates) + 1)
            suffix_metric_mins = [
                [0.0] * len(context.prepared.constraints)
                for _ in range(len(slot_candidates) + 1)
            ]
            suffix_metric_maxes = [
                [0.0] * len(context.prepared.constraints)
                for _ in range(len(slot_candidates) + 1)
            ]
            for depth in range(len(slot_candidates) - 1, -1, -1):
                slot_index, options = slot_candidates[depth]
                suffix_objective[depth] = suffix_objective[depth + 1] + max(
                    option.objective_value for option in options
                )
                for constraint_index, _constraint in enumerate(context.prepared.constraints):
                    metric_pos = context.constraint_metric_indices[constraint_index]
                    suffix_metric_mins[depth][constraint_index] = (
                        suffix_metric_mins[depth + 1][constraint_index]
                        + min(option.metric_values[metric_pos] for option in options)
                    )
                    suffix_metric_maxes[depth][constraint_index] = (
                        suffix_metric_maxes[depth + 1][constraint_index]
                        + max(option.metric_values[metric_pos] for option in options)
                    )

            def leaf_dfs(depth: int, running_objective: float) -> None:
                if stop_event is not None and stop_event.is_set():
                    return
                if running_objective + suffix_objective[depth] <= current_threshold():
                    return

                for constraint_index, constraint in enumerate(context.prepared.constraints):
                    metric_pos = context.constraint_metric_indices[constraint_index]
                    current_value = metric_totals[metric_pos]
                    min_possible = current_value + suffix_metric_mins[depth][constraint_index]
                    max_possible = current_value + suffix_metric_maxes[depth][constraint_index]
                    feasible_min, feasible_max = self._exact_constraint_feasibility_bounds(
                        constraint,
                        min_possible,
                        max_possible,
                    )
                    if constraint.operator in {">=", ">"} and feasible_max < constraint.target:
                        return
                    if constraint.operator in {"<=", "<"} and feasible_min > constraint.target:
                        return
                    if constraint.operator == "=" and not (feasible_min <= constraint.target <= feasible_max):
                        return

                if depth >= len(slot_candidates):
                    option = self._build_option_from_ingredient_names(
                        context.prepared.base_result.selection,
                        tuple(ingredient_names),
                        context.prepared.objective,
                        context.prepared.constraints,
                        context.prepared.roll_mode,
                    )
                    if option is not None:
                        push_option(option)
                    return

                slot_index, options = slot_candidates[depth]
                for option in options:
                    ingredient_names[slot_index] = option.ingredient_name
                    for metric_pos, metric_value in enumerate(option.metric_values):
                        metric_totals[metric_pos] += metric_value
                    leaf_dfs(depth + 1, running_objective + option.objective_value)
                    for metric_pos, metric_value in enumerate(option.metric_values):
                        metric_totals[metric_pos] -= metric_value
                    ingredient_names[slot_index] = "No Ingredient"

            leaf_dfs(0, context.base_objective_value)

        def pattern_dfs(depth: int) -> None:
            nonlocal explored_layouts
            if stop_event is not None and stop_event.is_set():
                return
            upper_bound = branch_upper_bound(depth)
            if upper_bound is None or upper_bound <= current_threshold():
                return
            if depth >= len(context.open_slot_order):
                explored_layouts += 1
                maybe_emit_progress(
                    f"Checked {explored_layouts:,}/{total_layouts:,} positional layouts."
                )
                search_leaf()
                return

            slot_index = context.open_slot_order[depth]
            child_patterns: list[tuple[float, tuple[tuple[str, int], ...]]] = []
            for pattern_signature in context.available_patterns:
                delta_vector = context.delta_by_slot_pattern[slot_index][pattern_signature]
                for target_index, value in enumerate(delta_vector):
                    current_effect_delta[target_index] += value
                assigned_patterns[slot_index] = pattern_signature
                child_upper_bound = branch_upper_bound(depth + 1)
                if child_upper_bound is not None:
                    child_patterns.append((child_upper_bound, pattern_signature))
                for target_index, value in enumerate(delta_vector):
                    current_effect_delta[target_index] -= value
                del assigned_patterns[slot_index]

            child_patterns.sort(key=lambda entry: entry[0], reverse=True)
            for _child_bound, pattern_signature in child_patterns:
                delta_vector = context.delta_by_slot_pattern[slot_index][pattern_signature]
                for target_index, value in enumerate(delta_vector):
                    current_effect_delta[target_index] += value
                assigned_patterns[slot_index] = pattern_signature
                pattern_dfs(depth + 1)
                for target_index, value in enumerate(delta_vector):
                    current_effect_delta[target_index] -= value
                del assigned_patterns[slot_index]

        pattern_dfs(0)
        if progress_callback is not None:
            progress_callback(
                list(ranked_options),
                explored_layouts,
                total_layouts,
                time.perf_counter() - started,
                f"Checked {explored_layouts:,}/{total_layouts:,} positional layouts.",
            )
        return ranked_options

    def _generate_exact(
        self,
        prepared: PreparedCraftSearch,
        top_n: int,
        stop_event: threading.Event | None,
        progress_callback: Callable[[list[CraftSearchOption], int, int, float, str], None] | None,
    ) -> list[CraftSearchOption]:
        started = time.perf_counter()
        next_progress = started + self.PROGRESS_INTERVAL_SECONDS
        if not prepared.open_slots:
            single = self._build_option_from_selection(
                prepared.base_result.selection,
                prepared.objective,
                prepared.constraints,
                prepared.roll_mode,
            )
            return [single] if single is not None else []

        current_names = list(prepared.base_result.selection.ingredient_names)
        ranked_options: list[CraftSearchOption] = []
        option_signatures: set[tuple[str, ...]] = set()
        explored = 0

        def maybe_emit_progress(detail: str) -> None:
            nonlocal next_progress
            if progress_callback is None:
                return
            now = time.perf_counter()
            if now < next_progress:
                return
            next_progress = now + self.PROGRESS_INTERVAL_SECONDS
            progress_callback(
                list(ranked_options),
                explored,
                prepared.total_states,
                now - started,
                detail,
            )

        def push_option(option: CraftSearchOption) -> None:
            if option.selection_values in option_signatures:
                return
            option_signatures.add(option.selection_values)
            ranked_options.append(option)
            ranked_options.sort(key=lambda value: value.objective_value, reverse=True)
            if len(ranked_options) > top_n:
                removed = ranked_options.pop()
                option_signatures.discard(removed.selection_values)

        def search(depth: int) -> None:
            nonlocal explored
            if stop_event and stop_event.is_set():
                return
            if depth >= len(prepared.slot_order):
                explored += 1
                option = self._build_option_from_ingredient_names(
                    prepared.base_result.selection,
                    tuple(current_names),
                    prepared.objective,
                    prepared.constraints,
                    prepared.roll_mode,
                )
                if option is not None:
                    push_option(option)
                maybe_emit_progress(
                    f"Checked {explored:,}/{prepared.total_states:,} filtered combinations."
                )
                return

            slot_index = prepared.slot_order[depth]
            for ingredient_name in prepared.candidate_names_by_slot[slot_index]:
                current_names[slot_index] = ingredient_name
                search(depth + 1)
                if stop_event and stop_event.is_set():
                    return
            current_names[slot_index] = prepared.base_result.selection.ingredient_names[slot_index]

        search(0)
        if progress_callback is not None:
            progress_callback(
                list(ranked_options),
                explored,
                prepared.total_states,
                time.perf_counter() - started,
                f"Checked {explored:,}/{prepared.total_states:,} filtered combinations.",
            )
        return ranked_options

    def _generate_mcts(
        self,
        prepared: PreparedCraftSearch,
        top_n: int,
        stop_event: threading.Event | None,
        progress_callback: Callable[[list[CraftSearchOption], int, int, float, str], None] | None,
    ) -> list[CraftSearchOption]:
        started = time.perf_counter()
        next_progress = started + self.PROGRESS_INTERVAL_SECONDS
        if not prepared.open_slots:
            single = self._build_option_from_selection(
                prepared.base_result.selection,
                prepared.objective,
                prepared.constraints,
                prepared.roll_mode,
            )
            return [single] if single is not None else []

        ranked_options: list[CraftSearchOption] = []
        option_signatures: set[tuple[str, ...]] = set()
        root = CraftMCTSNode(
            depth=0,
            assignments=tuple(),
            parent=None,
            untried_candidates=list(prepared.candidate_names_by_slot[prepared.slot_order[0]]),
        )
        iterations = 0

        def push_option(option: CraftSearchOption) -> None:
            if option.selection_values in option_signatures:
                return
            option_signatures.add(option.selection_values)
            ranked_options.append(option)
            ranked_options.sort(key=lambda value: value.objective_value, reverse=True)
            if len(ranked_options) > top_n:
                removed = ranked_options.pop()
                option_signatures.discard(removed.selection_values)

        while True:
            if stop_event and stop_event.is_set():
                break
            if root.fully_explored:
                break
            if iterations >= self.MCTS_MAX_ITERATIONS:
                break

            iterations += 1
            node = root
            while node.children and not node.untried_candidates and not node.fully_explored:
                node = self._select_mcts_child(node)

            if node.depth < len(prepared.slot_order) and node.untried_candidates:
                next_choice = node.untried_candidates.pop(
                    self._random.randrange(len(node.untried_candidates))
                )
                child_depth = node.depth + 1
                child = CraftMCTSNode(
                    depth=child_depth,
                    assignments=node.assignments + (next_choice,),
                    parent=node,
                    untried_candidates=(
                        list(prepared.candidate_names_by_slot[prepared.slot_order[child_depth]])
                        if child_depth < len(prepared.slot_order)
                        else []
                    ),
                )
                node.children.append(child)
                node = child

            option, reward = self._rollout_and_evaluate(prepared, node.assignments)
            if option is not None:
                push_option(option)
            self._backpropagate(node, reward)
            self._mark_fully_explored(node)

            if progress_callback is not None:
                now = time.perf_counter()
                if now >= next_progress:
                    next_progress = now + self.PROGRESS_INTERVAL_SECONDS
                    progress_callback(
                        list(ranked_options),
                        iterations,
                        prepared.total_states,
                        now - started,
                        f"Completed {iterations:,} MCTS iterations across {prepared.total_states:,} filtered combinations.",
                    )

        if progress_callback is not None:
            progress_callback(
                list(ranked_options),
                iterations,
                prepared.total_states,
                time.perf_counter() - started,
                f"Completed {iterations:,} MCTS iterations across {prepared.total_states:,} filtered combinations.",
            )
        return ranked_options

    def _valid_ingredient_names_for_recipe(self, recipe: Recipe) -> tuple[str, ...]:
        cache_key = (recipe.skill, recipe.lvl[1])
        cached = self._valid_ingredient_cache.get(cache_key)
        if cached is not None:
            return cached
        names = tuple(
            ingredient.display_name
            for ingredient in self.data.ingredients
            if recipe.skill in ingredient.skills and ingredient.lvl <= recipe.lvl[1]
        )
        self._valid_ingredient_cache[cache_key] = names
        return names

    def _result_with_replacement(
        self,
        base_selection: CraftSelection,
        slot_index: int,
        ingredient_name: str,
    ) -> CraftResult:
        ingredient_names = list(base_selection.ingredient_names)
        ingredient_names[slot_index] = ingredient_name
        selection = CraftSelection(
            recipe_name=base_selection.recipe_name,
            level_range=base_selection.level_range,
            mat_tiers=base_selection.mat_tiers,
            ingredient_names=tuple(ingredient_names),
            attack_speed=base_selection.attack_speed,
        )
        return self.data.craft(selection)

    def _build_option_from_selection(
        self,
        selection: CraftSelection,
        objective: OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
        roll_mode: str,
    ) -> CraftSearchOption | None:
        return self._build_option_from_ingredient_names(
            selection,
            selection.ingredient_names,
            objective,
            constraints,
            roll_mode,
        )

    def _build_option_from_ingredient_names(
        self,
        template_selection: CraftSelection,
        ingredient_names: tuple[str, ...],
        objective: OptimizationObjective,
        constraints: tuple[OptimizationConstraint, ...],
        roll_mode: str,
    ) -> CraftSearchOption | None:
        selection = CraftSelection(
            recipe_name=template_selection.recipe_name,
            level_range=template_selection.level_range,
            mat_tiers=template_selection.mat_tiers,
            ingredient_names=ingredient_names,
            attack_speed=template_selection.attack_speed,
        )
        result = self.data.craft(selection)
        if result.warnings:
            return None

        constraint_values = {
            constraint.display_label(): self.metric_value_from_result(result, constraint.metric_key, roll_mode)
            for constraint in constraints
        }
        if not all(
            self._constraint_matches(
                constraint_values[constraint.display_label()],
                constraint,
            )
            for constraint in constraints
        ):
            return None

        objective_value = self.objective_value_from_result(result, objective, roll_mode)
        return CraftSearchOption(
            result=result,
            objective_label=objective.display_label(),
            objective_value=objective_value,
            objective=objective,
            roll_mode=roll_mode,
            constraint_values=constraint_values,
        )

    def _rollout_and_evaluate(
        self,
        prepared: PreparedCraftSearch,
        assignments: tuple[str, ...],
    ) -> tuple[CraftSearchOption | None, float]:
        current_names = list(prepared.base_result.selection.ingredient_names)
        for depth, ingredient_name in enumerate(assignments):
            current_names[prepared.slot_order[depth]] = ingredient_name

        for depth in range(len(assignments), len(prepared.slot_order)):
            slot_index = prepared.slot_order[depth]
            candidates = prepared.candidate_names_by_slot[slot_index]
            current_names[slot_index] = self._rollout_choice(candidates)

        selection = CraftSelection(
            recipe_name=prepared.base_result.selection.recipe_name,
            level_range=prepared.base_result.selection.level_range,
            mat_tiers=prepared.base_result.selection.mat_tiers,
            ingredient_names=tuple(current_names),
            attack_speed=prepared.base_result.selection.attack_speed,
        )
        result = self.data.craft(selection)
        metric_values = {
            term.metric_key: self.metric_value_from_result(result, term.metric_key, prepared.roll_mode)
            for term in prepared.objective.terms
        }
        for constraint in prepared.constraints:
            metric_values.setdefault(
                constraint.metric_key,
                self.metric_value_from_result(result, constraint.metric_key, prepared.roll_mode),
            )

        scaled_objective = self._objective_value_from_metric_values(
            metric_values,
            prepared.objective,
            scaled=True,
        )
        reward = scaled_objective - (self._constraint_penalty_sum(metric_values, prepared.constraints) * 3.0)
        if result.warnings:
            return None, reward - 10.0

        if not all(
            self._constraint_matches(metric_values[constraint.metric_key], constraint)
            for constraint in prepared.constraints
        ):
            return None, reward

        option = CraftSearchOption(
            result=result,
            objective_label=prepared.objective.display_label(),
            objective_value=self._objective_value_from_metric_values(
                metric_values,
                prepared.objective,
                scaled=False,
            ),
            objective=prepared.objective,
            roll_mode=prepared.roll_mode,
            constraint_values={
                constraint.display_label(): metric_values[constraint.metric_key]
                for constraint in prepared.constraints
            },
        )
        return option, reward

    def _rollout_choice(self, candidates: tuple[str, ...]) -> str:
        if len(candidates) <= 1:
            return candidates[0]
        top_slice = candidates[: min(6, len(candidates))]
        weights = list(range(len(top_slice), 0, -1))
        return self._random.choices(top_slice, weights=weights, k=1)[0]

    def _select_mcts_child(self, node: CraftMCTSNode) -> CraftMCTSNode:
        parent_visits = max(1, node.visits)
        best_child = node.children[0]
        best_score = float("-inf")
        for child in node.children:
            if child.fully_explored:
                continue
            exploitation = child.total_reward / max(1, child.visits)
            exploration = math.sqrt(math.log(parent_visits + 1) / max(1, child.visits))
            score = exploitation + (1.35 * exploration)
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def _backpropagate(self, node: CraftMCTSNode, reward: float) -> None:
        current: CraftMCTSNode | None = node
        while current is not None:
            current.visits += 1
            current.total_reward += reward
            current.best_reward = max(current.best_reward, reward)
            current = current.parent

    def _mark_fully_explored(self, node: CraftMCTSNode) -> None:
        current: CraftMCTSNode | None = node
        while current is not None:
            current.fully_explored = bool(
                not current.untried_candidates
                and all(child.fully_explored for child in current.children)
                and (current.depth > 0 or current.children)
            )
            current = current.parent

    def _select_slot_candidates(
        self,
        candidates: list[IngredientCandidate],
        objective: OptimizationObjective,
        constraints: list[OptimizationConstraint],
        cap: int,
    ) -> list[IngredientCandidate]:
        if not candidates:
            return []

        by_name = {candidate.ingredient_name: candidate for candidate in candidates}
        ranked = sorted(
            candidates,
            key=self._candidate_retention_key,
            reverse=True,
        )
        selected_names: set[str] = {"No Ingredient"}

        def take_candidates(ordered: list[IngredientCandidate], count: int) -> None:
            for candidate in ordered[:count]:
                selected_names.add(candidate.ingredient_name)

        take_candidates(ranked, self.PRIMARY_SLOT_KEEP)
        positional_seed_order = sorted(
            (
                candidate
                for candidate in candidates
                if candidate.positive_interaction_score > 0.0 and candidate.direct_effect_score <= 0.0
            ),
            key=lambda candidate: (
                candidate.positive_interaction_score,
                candidate.utility,
                candidate.interaction_score,
            ),
            reverse=True,
        )
        take_candidates(positional_seed_order, self.POSITIONAL_SEED_KEEP)
        for term in objective.terms:
            term_order = sorted(
                candidates,
                key=lambda candidate: candidate.metric_values.get(term.metric_key, 0.0),
                reverse=True,
            )
            take_candidates(term_order, self.TERM_SLOT_KEEP)

        for constraint in constraints:
            if constraint.operator in {">=", ">"}:
                constraint_order = sorted(
                    candidates,
                    key=lambda candidate: candidate.metric_values.get(constraint.metric_key, 0.0),
                    reverse=True,
                )
            elif constraint.operator in {"<=", "<"}:
                constraint_order = sorted(
                    candidates,
                    key=lambda candidate: candidate.metric_values.get(constraint.metric_key, 0.0),
                )
            else:
                constraint_order = sorted(
                    candidates,
                    key=lambda candidate: abs(candidate.metric_values.get(constraint.metric_key, 0.0) - constraint.target),
                )
            take_candidates(constraint_order, self.CONSTRAINT_SLOT_KEEP)

        interaction_order = sorted(
            candidates,
            key=lambda candidate: candidate.interaction_score,
            reverse=True,
        )
        take_candidates(interaction_order, self.INTERACTION_SLOT_KEEP)

        ordered_selected = [by_name[name] for name in selected_names if name in by_name]
        ordered_selected.sort(key=self._candidate_retention_key, reverse=True)
        if len(ordered_selected) <= cap:
            return ordered_selected

        trimmed = ordered_selected[:cap]
        if all(candidate.ingredient_name != "No Ingredient" for candidate in trimmed) and "No Ingredient" in by_name:
            trimmed[-1] = by_name["No Ingredient"]
            trimmed.sort(key=self._candidate_retention_key, reverse=True)
        return trimmed

    def _trim_exact_candidate_pool(
        self,
        candidate_names_by_slot: dict[int, tuple[str, ...]],
        protected_names_by_slot: dict[int, set[str]] | None = None,
    ) -> dict[int, tuple[str, ...]]:
        trimmed = {
            slot_index: list(candidate_names)
            for slot_index, candidate_names in candidate_names_by_slot.items()
        }
        protected = protected_names_by_slot or {}
        while True:
            total_states = 1
            for candidate_names in trimmed.values():
                total_states *= max(1, len(candidate_names))
            if total_states <= self.EXACT_MAX_STATES:
                break

            removal = self._select_exact_removal(trimmed, protected, allow_protected=False)
            if removal is None:
                removal = self._select_exact_removal(trimmed, protected, allow_protected=True)
            if removal is None:
                break

            removable_slot, remove_index = removal
            del trimmed[removable_slot][remove_index]

        return {
            slot_index: tuple(candidate_names)
            for slot_index, candidate_names in trimmed.items()
        }

    def _select_exact_protected_names(
        self,
        ordered_candidates: list[IngredientCandidate],
        objective: OptimizationObjective,
        constraints: list[OptimizationConstraint],
    ) -> set[str]:
        protected_names: set[str] = {"No Ingredient"}
        if not ordered_candidates:
            return protected_names

        per_term_keep = max(
            1,
            math.ceil(self.EXACT_OBJECTIVE_PROTECT_BUDGET / max(1, len(objective.terms))),
        )
        for term in objective.terms:
            term_order = sorted(
                ordered_candidates,
                key=lambda candidate: candidate.metric_values.get(term.metric_key, 0.0),
                reverse=True,
            )
            for candidate in term_order[:per_term_keep]:
                protected_names.add(candidate.ingredient_name)

        for constraint in constraints:
            if constraint.operator in {">=", ">"}:
                constraint_order = sorted(
                    ordered_candidates,
                    key=lambda candidate: candidate.metric_values.get(constraint.metric_key, 0.0),
                    reverse=True,
                )
            elif constraint.operator in {"<=", "<"}:
                constraint_order = sorted(
                    ordered_candidates,
                    key=lambda candidate: candidate.metric_values.get(constraint.metric_key, 0.0),
                )
            else:
                constraint_order = sorted(
                    ordered_candidates,
                    key=lambda candidate: abs(
                        candidate.metric_values.get(constraint.metric_key, 0.0) - constraint.target
                    ),
                )
            for candidate in constraint_order[: self.EXACT_CONSTRAINT_PROTECT]:
                protected_names.add(candidate.ingredient_name)
        return protected_names

    def _select_exact_removal(
        self,
        trimmed: dict[int, list[str]],
        protected_names_by_slot: dict[int, set[str]],
        allow_protected: bool,
    ) -> tuple[int, int] | None:
        removable_slot = None
        removable_index = None
        removable_length = -1
        for slot_index, candidate_names in trimmed.items():
            if len(candidate_names) <= self.EXACT_MIN_SLOT_CANDIDATES:
                continue
            remove_index = self._find_exact_removal_index(
                candidate_names,
                protected_names_by_slot.get(slot_index, set()),
                allow_protected=allow_protected,
            )
            if remove_index is None:
                continue
            if len(candidate_names) > removable_length:
                removable_length = len(candidate_names)
                removable_slot = slot_index
                removable_index = remove_index

        if removable_slot is None or removable_index is None:
            return None
        return removable_slot, removable_index

    @staticmethod
    def _find_exact_removal_index(
        candidate_names: list[str],
        protected_names: set[str],
        allow_protected: bool,
    ) -> int | None:
        for remove_index in range(len(candidate_names) - 1, -1, -1):
            ingredient_name = candidate_names[remove_index]
            if ingredient_name == "No Ingredient":
                continue
            if allow_protected or ingredient_name not in protected_names:
                return remove_index
        if allow_protected and candidate_names:
            return len(candidate_names) - 1
        return None

    @staticmethod
    def _candidate_retention_key(candidate: IngredientCandidate) -> tuple[float, float, float, float, bool]:
        negative_interaction_score = max(0.0, candidate.interaction_score - candidate.positive_interaction_score)
        seed_bonus = (candidate.positive_interaction_score * 0.35) - (negative_interaction_score * 0.05)
        return (
            candidate.utility + seed_bonus,
            candidate.positive_interaction_score,
            -negative_interaction_score,
            candidate.objective_value,
            candidate.ingredient_name != "No Ingredient",
        )

    def _calibrate_objective(
        self,
        objective: OptimizationObjective,
        sampled_results: list[CraftResult],
        roll_mode: str,
    ) -> OptimizationObjective:
        scales: list[float] = []
        for term in objective.terms:
            values = [
                abs(self.metric_value_from_result(result, term.metric_key, roll_mode))
                for result in sampled_results
            ]
            scales.append(max(1.0, max(values, default=1.0)))
        return objective.with_scales(scales)

    def _objective_value_from_metric_values(
        self,
        metric_values: dict[str, float],
        objective: OptimizationObjective,
        scaled: bool,
    ) -> float:
        if objective.is_single_metric():
            raw_value = metric_values.get(objective.primary_metric_key(), 0.0)
            if scaled:
                return raw_value / objective.scale_for_index(0, raw_value)
            return raw_value

        total = 0.0
        for index, term in enumerate(objective.terms):
            raw_value = metric_values.get(term.metric_key, 0.0)
            total += objective.normalized_weight(index) * (
                raw_value / objective.scale_for_index(index, raw_value)
            )
        return total

    @staticmethod
    def _constraint_matches(value: float, constraint: OptimizationConstraint) -> bool:
        if constraint.operator == ">=":
            return value >= constraint.target
        if constraint.operator == "<=":
            return value <= constraint.target
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
        if constraint.operator in {">=", ">"}:
            return max(0.0, constraint.target - value) / scale
        if constraint.operator in {"<=", "<"}:
            return max(0.0, value - constraint.target) / scale
        if constraint.operator == "=":
            return abs(value - constraint.target) / scale
        raise ValueError(f"Unsupported constraint operator: {constraint.operator}")

    def _constraint_penalty_sum(
        self,
        metric_values: dict[str, float],
        constraints: Iterable[OptimizationConstraint],
    ) -> float:
        total = 0.0
        for constraint in constraints:
            total += self._constraint_penalty(metric_values.get(constraint.metric_key, 0.0), constraint)
        return total

    def _weapon_damage_avg(self, result: CraftResult, roll_mode: str) -> float:
        if not result.damage_rows:
            return 0.0
        row_total = 0.0
        for _label, low_text, high_text in result.damage_rows:
            low_range = parse_range(low_text)
            high_range = parse_range(high_text)
            low_average = (low_range[0] + low_range[1]) / 2.0
            high_average = (high_range[0] + high_range[1]) / 2.0
            row_total += self._pick_roll_value(low_average, high_average, roll_mode)
        return row_total

    def _hp_metric_value(self, result: CraftResult, roll_mode: str) -> float:
        stat_map = result.stat_map
        if stat_map.get("category") == "armor":
            return self._pick_roll_value(
                float(stat_map.get("hpLow", 0)),
                float(stat_map.get("hp", 0)),
                roll_mode,
            )
        raw_hp = stat_map.get("hp", 0)
        if isinstance(raw_hp, str) and "-" in raw_hp:
            low_value, high_value = parse_range(raw_hp)
            return self._pick_roll_value(float(low_value), float(high_value), roll_mode)
        return float(raw_hp or 0.0)

    @staticmethod
    def _pick_pair_value(values: Iterable[int], roll_mode: str) -> float:
        low_value, high_value = tuple(values)
        return CrafterOptimizer._pick_roll_value(float(low_value), float(high_value), roll_mode)

    @staticmethod
    def _pick_roll_value(low_value: float, high_value: float, roll_mode: str) -> float:
        if roll_mode == "worst":
            return low_value
        if roll_mode == "best":
            return high_value
        return (low_value + high_value) / 2.0

    @staticmethod
    def _normalize_roll_mode(roll_mode: str) -> str:
        normalized = (roll_mode or "average").strip().lower()
        if normalized not in ROLL_MODE_LABELS:
            return "average"
        return normalized
