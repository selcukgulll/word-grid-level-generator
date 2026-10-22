# Algorithm notes

## Problem formulation

For a list of distinct words and a fixed `rows × columns` grid, choose one starting cell and direction (right or down) for each word. Every placement must stay in bounds. At intersections, letters must match. A cell cannot be occupied by two words with the same direction. Non-crossing cells must not touch occupied cells perpendicularly; cells immediately before and after a word must be empty. Optionally require every word after the first to share at least one letter with the previously placed group.

## Search procedure

1. Normalize input words to uppercase and order by decreasing length.
2. Enumerate in-bounds placements and shuffle them using a local, user-supplied random seed.
3. Reject placements that conflict with occupied cells or violate adjacency constraints.
4. Prefer placements creating more intersections (a heuristic, not a guarantee of best layout).
5. Apply a valid candidate, recurse, and undo it if downstream words cannot be placed.
6. Stop after the first complete board or when the visited-node budget is reached.
7. For multiple level candidates, vary the random seed, deduplicate complete grids, and rank samples by intersections and compactness.

This is **seeded randomized backtracking** with search bounds. It is not an exhaustive enumeration of all possible grids, a SAT solver, or an optimizer that guarantees the best board. The node budget can interrupt an otherwise solvable input. Similarly, a fixed word ordering can miss solutions that require a different insertion order when connected-mode is enabled.

## Metrics

- **Intersections:** sum of all placed word lengths minus number of occupied cells; for valid layouts this counts shared cells.
- **Fill ratio:** occupied cells divided by all cells in the board.
- **Compactness:** occupied cells divided by area of their minimal axis-aligned bounding rectangle.
- **Visited nodes:** candidate placements actually tried during recursive search; lower is not necessarily easier gameplay.

These are **geometric diagnostics**. They do not measure human solving time, puzzle difficulty, player satisfaction, semantic quality, or a level progression curve.

## Limitations / ideas for further experiments

- Benchmark candidate generation and search time as grid size, word list length, and word overlap vary.
- Experiment with different insertion orders, variable-ordering heuristics, and forward checking.
- Add constraints for theme, word frequency, symmetry, board silhouette, and target difficulty.
- Generate more than one board per seed by exploring alternative solutions and deduplicate under rotations/reflections.
- Validate puzzle difficulty using players or an independent solver rather than assuming density predicts difficulty.
- Turkish uppercase conversion is not locale-aware (`i` becomes `I` in Python). Supply capital `İ` explicitly where applicable.

## Benchmark protocol

`python -m wordgrid.benchmark --seeds 20 --max-nodes 20000` evaluates four publicly reproducible toy cases, one trial per seed `0..19`. A `layouts_found / seeds_tested` ratio measures how many configured searches found solutions *under this exact heuristic and budget*. Failed trials must not be interpreted as proof that no board can exist.
