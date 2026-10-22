"""Reproducible small-scale stress tests for the search algorithm."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from .generator import generate_board
from .levels import layout_metrics

CONFIGS = [
    ("turkish_3x4", ["AİLE", "ELA", "ARI"], 3, 4),
    ("short_words_7x7", ["CAT", "ART", "TAR"], 7, 7),
    ("mobile_theme_10x10", ["CODE", "DATA", "GAME", "MODEL"], 10, 10),
    ("dense_6x6", ["CODE", "DATA", "GAME", "MODEL"], 6, 6),
]


def run_benchmark(seeds: range = range(20), max_nodes: int = 20_000) -> list[dict]:
    if max_nodes < 1:
        raise ValueError("max_nodes must be positive")
    results = []
    for name, words, rows, cols in CONFIGS:
        nodes, compacts, crossings = [], [], []
        for seed in seeds:
            board = generate_board(words, rows, cols, seed=seed, max_nodes=max_nodes)
            if board is None:
                continue
            metrics = layout_metrics(board)
            nodes.append(board.visited_nodes)
            compacts.append(metrics["compactness"])
            crossings.append(metrics["intersection_count"])
        results.append({
            "configuration": name,
            "board": f"{rows}x{cols}",
            "words": words,
            "seeds_tested": len(seeds),
            "layouts_found": len(nodes),
            "solved_fraction": len(nodes) / len(seeds) if seeds else None,
            "median_nodes_on_success": statistics.median(nodes) if nodes else None,
            "median_compactness_on_success": statistics.median(compacts) if compacts else None,
            "median_intersections_on_success": statistics.median(crossings) if crossings else None,
            "max_nodes_per_trial": max_nodes,
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--max-nodes", type=int, default=20_000)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.json"))
    args = parser.parse_args()
    if args.seeds < 1 or args.max_nodes < 1:
        parser.error("--seeds and --max-nodes must be positive")
    result = {
        "note": "Exploratory toy benchmark; results are not production performance guarantees.",
        "seed_range": [0, args.seeds - 1],
        "results": run_benchmark(range(args.seeds), args.max_nodes),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved benchmark: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
