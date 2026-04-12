from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from WynnBuilder.build_tester import (  # noqa: E402
    DATA_PATH,
    BuildOptimizer,
    OptimizationConstraint,
    WynnBuildEngine,
    default_mcts_worker_count,
    make_optimization_objective,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark representative WynnBuilder search workloads.",
    )
    parser.add_argument(
        "--mcts-window-seconds",
        type=float,
        default=0.75,
        help="How long to let the in-process MCTS run before stopping each benchmark case.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of result candidates to keep during the benchmark.",
    )
    return parser.parse_args()


def benchmark_case(
    optimizer: BuildOptimizer,
    engine: WynnBuildEngine,
    name: str,
    objective_metric: str,
    constraints: list[OptimizationConstraint],
    top_n: int,
    mcts_window_seconds: float,
) -> None:
    objective = make_optimization_objective(((objective_metric, 1.0),))

    started = time.perf_counter()
    prepared = optimizer._prepare_search({}, objective, constraints, engine.max_item_level)
    prepare_seconds = time.perf_counter() - started

    started = time.perf_counter()
    optimizer._prepare_search({}, objective, constraints, engine.max_item_level)
    cached_prepare_seconds = time.perf_counter() - started

    started = time.perf_counter()
    estimate = optimizer.estimate_exact_search(
        {},
        objective,
        constraints,
        top_n,
        engine.max_item_level,
        prepared_space=prepared,
    )
    exact_estimate_seconds = time.perf_counter() - started

    stop_event = threading.Event()
    first_progress_seconds: float | None = None
    mcts_started = time.perf_counter()

    def stop_later() -> None:
        time.sleep(max(0.05, mcts_window_seconds))
        stop_event.set()

    def progress_callback(_options, _iterations, _valid_count, elapsed: float, _detail: str) -> None:
        nonlocal first_progress_seconds
        if first_progress_seconds is None:
            first_progress_seconds = elapsed

    stopper = threading.Thread(target=stop_later, daemon=True)
    stopper.start()
    options = optimizer.generate_mcts(
        {},
        None,
        objective,
        constraints,
        top_n,
        engine.max_item_level,
        stop_event=stop_event,
        progress_callback=progress_callback,
        prepared_space=prepared,
    )
    mcts_seconds = time.perf_counter() - mcts_started

    print(name)
    print(f"  objective: {objective_metric}")
    if constraints:
        constraint_text = ", ".join(f"{constraint.metric_key} {constraint.operator} {constraint.target:g}" for constraint in constraints)
        print(f"  constraints: {constraint_text}")
    else:
        print("  constraints: none")
    print(f"  candidate preparation: {prepare_seconds:.3f}s")
    print(f"  cached preparation rerun: {cached_prepare_seconds:.3f}s")
    if estimate.sampled_states > 0:
        exact_detail = f"sampled {estimate.sampled_states:,} states, est. {estimate.estimated_total_states:,}"
    else:
        exact_detail = "seeded initial frontier before the sample loop"
    print(f"  exact estimate sample: {exact_estimate_seconds:.3f}s ({exact_detail})")
    print(
        "  mcts startup window: "
        f"{mcts_seconds:.3f}s "
        f"(first progress {first_progress_seconds:.3f}s, {len(options)} option(s))"
        if first_progress_seconds is not None
        else f"  mcts startup window: {mcts_seconds:.3f}s (no progress callback before stop, {len(options)} option(s))"
    )
    print(f"  group sizes: {[len(group) for group in prepared.group_candidates]}")
    print("")


def main() -> int:
    args = parse_args()
    engine = WynnBuildEngine(DATA_PATH)
    optimizer = BuildOptimizer(engine)

    cases = [
        ("HP Total", "hp_total", []),
        ("Melee Avg", "melee_avg", []),
        ("Spell Avg", "spell_avg", []),
        (
            "Spell Avg + Common Constraints",
            "spell_avg",
            [
                OptimizationConstraint("mr", ">", 5.0),
                OptimizationConstraint("hp_total", ">", 4000.0),
                OptimizationConstraint("spd", ">", 20.0),
            ],
        ),
    ]

    print("WynnBuilder benchmark")
    print(f"  data: {DATA_PATH}")
    print(f"  top_n: {args.top_n}")
    print(f"  mcts window: {args.mcts_window_seconds:.2f}s")
    print(f"  default workers (GUI): {default_mcts_worker_count()}")
    print("")

    for name, objective_metric, constraints in cases:
        benchmark_case(
            optimizer,
            engine,
            name,
            objective_metric,
            constraints,
            args.top_n,
            args.mcts_window_seconds,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
