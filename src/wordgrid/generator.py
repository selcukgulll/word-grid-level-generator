"""Constrained word-grid generation with seeded, randomized backtracking.

Word placements run left-to-right or top-to-bottom. Perpendicular words may
intersect on matching letters; parallel overlap and unintended adjacent words
are rejected. This is an experimental generator, not a full crossword editor.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Placement:
    word: str
    row: int
    col: int
    orientation: str  # H or V


@dataclass
class BoardResult:
    grid: list[list[str | None]]
    placements: list[Placement]
    visited_nodes: int

    def as_text(self) -> str:
        width = len(self.grid[0])
        header = "    " + " ".join(f"{i:2}" for i in range(width))
        lines = [header]
        for index, row in enumerate(self.grid):
            lines.append(f"{index:2}  " + " ".join(f"{ch or '·':>2}" for ch in row))
        return "\n".join(lines)


def generate_board(
    words: list[str],
    rows: int,
    cols: int,
    *,
    seed: int = 42,
    require_connected: bool = True,
    max_nodes: int = 100_000,
) -> BoardResult | None:
    """Find a valid placement of all words or return None within the node budget.

    Reproducible for a fixed seed and Python version. The node cap prevents
    unbounded searches; returning None does not prove unsatisfiability.
    """
    if rows < 1 or cols < 1 or max_nodes < 1:
        raise ValueError("rows, cols, and max_nodes must be positive")
    cleaned = [word.strip().upper() for word in words]
    if not cleaned or any(len(word) < 2 or not word.isalpha() for word in cleaned):
        raise ValueError("Provide alphabetic words containing at least two letters")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Duplicate words are not supported")
    if any(len(word) > max(rows, cols) for word in cleaned):
        return None

    rng = random.Random(seed)
    # Placing longer words first usually reduces branching.
    ordered = sorted(cleaned, key=lambda w: (-len(w), w))
    grid: list[list[str | None]] = [[None for _ in range(cols)] for _ in range(rows)]
    directions: dict[tuple[int, int], set[str]] = {}
    placed: list[Placement] = []
    visited = 0

    def candidates(word: str):
        options: list[Placement] = []
        for orientation in ("H", "V"):
            dr, dc = (0, 1) if orientation == "H" else (1, 0)
            max_r = rows - (len(word) - 1) * dr
            max_c = cols - (len(word) - 1) * dc
            for r in range(max_r):
                for c in range(max_c):
                    options.append(Placement(word, r, c, orientation))
        rng.shuffle(options)
        return options

    def evaluate(option: Placement) -> int | None:
        dr, dc = (0, 1) if option.orientation == "H" else (1, 0)
        end_r = option.row + len(option.word) * dr
        end_c = option.col + len(option.word) * dc
        before_r, before_c = option.row - dr, option.col - dc
        if 0 <= before_r < rows and 0 <= before_c < cols and grid[before_r][before_c] is not None:
            return None
        if 0 <= end_r < rows and 0 <= end_c < cols and grid[end_r][end_c] is not None:
            return None
        intersections = 0
        for k, letter in enumerate(option.word):
            r, c = option.row + k * dr, option.col + k * dc
            original = grid[r][c]
            if original is not None:
                if original != letter or option.orientation in directions.get((r, c), set()):
                    return None
                intersections += 1
            else:
                neighbors = ((r - 1, c), (r + 1, c)) if option.orientation == "H" else ((r, c - 1), (r, c + 1))
                if any(0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] is not None for nr, nc in neighbors):
                    return None
        if require_connected and placed and intersections == 0:
            return None
        return intersections

    def search(index: int) -> bool:
        nonlocal visited
        if index == len(ordered):
            return True
        if visited >= max_nodes:
            return False
        word = ordered[index]
        options = [(overlap, option) for option in candidates(word) if (overlap := evaluate(option)) is not None]
        # Prefer connectivity when multiple candidates are available.
        options.sort(key=lambda pair: -pair[0])
        for _overlap, option in options:
            if visited >= max_nodes:
                return False
            # Revalidate since candidates are generated before other recursive search.
            if evaluate(option) is None:
                continue
            visited += 1
            dr, dc = (0, 1) if option.orientation == "H" else (1, 0)
            changed: list[tuple[int, int, bool]] = []
            for k, letter in enumerate(option.word):
                r, c = option.row + k * dr, option.col + k * dc
                already_filled = grid[r][c] is not None
                if not already_filled:
                    grid[r][c] = letter
                directions.setdefault((r, c), set()).add(option.orientation)
                changed.append((r, c, already_filled))
            placed.append(option)
            if search(index + 1):
                return True
            placed.pop()
            for r, c, already_filled in changed:
                directions[(r, c)].remove(option.orientation)
                if not directions[(r, c)]:
                    del directions[(r, c)]
                if not already_filled:
                    grid[r][c] = None
        return False

    if not search(0):
        return None
    return BoardResult([row[:] for row in grid], list(placed), visited)


