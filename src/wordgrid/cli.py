"""Command line interface for procedural word-grid design."""

from __future__ import annotations

import argparse
from pathlib import Path

from .levels import generate_variants, layout_metrics, to_json, to_svg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate connected or disconnected word-grid puzzle layouts."
    )
    parser.add_argument("--words", nargs="+", required=True,
                        help="Words to place (two letters minimum; e.g., AİLE ELA ARI)")
    parser.add_argument("--rows", type=int, default=7)
    parser.add_argument("--cols", type=int, default=7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=1, help="Unique layouts to return")
    parser.add_argument("--trials", type=int, default=60,
                        help="Number of trial seeds to explore (not exhaustive)")
    parser.add_argument("--max-nodes", type=int, default=20_000,
                        help="Maximum search nodes per trial")
    parser.add_argument("--allow-disconnected", action="store_true")
    parser.add_argument("--format", choices=["text", "json", "svg"], default="text")
    parser.add_argument("--output", type=Path,
                        help="Write to file instead of stdout")
    args = parser.parse_args()

    if args.format == "svg" and args.count != 1:
        parser.error("SVG export supports one board; use --count 1")

    try:
        levels = generate_variants(
            args.words, args.rows, args.cols, seed=args.seed,
            count=args.count, trials=args.trials, max_nodes=args.max_nodes,
            require_connected=not args.allow_disconnected,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if not levels:
        parser.exit(1, "No valid layout found within the trial/node budgets. "
                       "Try a larger grid, different words, or a higher budget.\n")

    if args.format == "json":
        content = to_json(levels)
    elif args.format == "svg":
        content = to_svg(levels[0])
    else:
        blocks = []
        for index, level in enumerate(levels, start=1):
            metrics = layout_metrics(level.board)
            blocks.append(f"Level {index} | seed {level.seed} | "
                          f"crossings {metrics['intersection_count']} | "
                          f"compactness {metrics['compactness']:.2f}\n"
                          f"{level.board.as_text()}\n" +
                          "\n".join(f"  {p.word:12s} {p.orientation} "
                                    f"@ ({p.row},{p.col})" for p in level.board.placements))
        content = "\n\n".join(blocks) + "\n"

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(f"Saved {len(levels)} level(s) to {args.output}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
