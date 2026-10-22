"""Sample distinct layouts, score their geometry, and export them as JSON/SVG."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape

from .generator import BoardResult, generate_board


@dataclass(frozen=True)
class LevelVariant:
    seed: int
    board: BoardResult


def layout_metrics(board: BoardResult) -> dict[str, float | int]:
    """Geometric descriptors, *not* estimates of human difficulty or fun."""
    grid = board.grid
    rows, cols = len(grid), len(grid[0])
    occupied = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] is not None]
    if not occupied:
        return {"fill_ratio": 0.0, "compactness": 0.0,
                "intersection_count": 0, "bounding_box_area": 0,
                "nodes_visited": board.visited_nodes}

    r_min = min(r for r, _ in occupied)
    r_max = max(r for r, _ in occupied)
    c_min = min(c for _, c in occupied)
    c_max = max(c for _, c in occupied)
    area = (r_max - r_min + 1) * (c_max - c_min + 1)
    total_letters = sum(len(p.word) for p in board.placements)
    # Valid boards allow at most one word per orientation in a cell.
    shared_cells = total_letters - len(occupied)
    return {
        "fill_ratio": round(len(occupied) / (rows * cols), 4),
        "compactness": round(len(occupied) / area, 4),
        "intersection_count": shared_cells,
        "bounding_box_area": area,
        "nodes_visited": board.visited_nodes,
    }


def generate_variants(
    words: list[str], rows: int, cols: int, *,
    seed: int = 42, count: int = 3, trials: int = 60,
    require_connected: bool = True, max_nodes: int = 100_000,
) -> list[LevelVariant]:
    """Generate unique boards from consecutive seeds; rank compactness and crossings.

    A smaller-than-requested return means fewer distinct layouts were found
    in the requested trial budget; it does NOT mean only that many exist.
    """
    if count < 1 or trials < 1:
        raise ValueError("count and trials must be positive")
    seen: set[tuple[tuple[str | None, ...], ...]] = set()
    levels: list[LevelVariant] = []
    for trial_seed in range(seed, seed + trials):
        board = generate_board(
            words, rows, cols, seed=trial_seed,
            require_connected=require_connected, max_nodes=max_nodes,
        )
        if board is None:
            continue
        signature = tuple(tuple(row) for row in board.grid)
        if signature in seen:
            continue
        seen.add(signature)
        levels.append(LevelVariant(trial_seed, board))
    levels.sort(key=lambda level: (
        -layout_metrics(level.board)["intersection_count"],
        -layout_metrics(level.board)["compactness"],
        layout_metrics(level.board)["bounding_box_area"],
        level.seed,
    ))
    return levels[:count]


def to_json(levels: list[LevelVariant]) -> str:
    """Engine-neutral JSON with grid, placements, and layout metrics."""
    payload = {
        "schema_version": 1,
        "coordinate_system": "zero-based row/column, top-left origin",
        "levels": [
            {
                "seed": level.seed,
                "rows": len(level.board.grid),
                "cols": len(level.board.grid[0]),
                "grid": level.board.grid,
                "placements": [
                    {"word": p.word, "row": p.row, "col": p.col, "orientation": p.orientation}
                    for p in level.board.placements
                ],
                "metrics": layout_metrics(level.board),
            }
            for level in levels
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def to_svg(level: LevelVariant, *, tile: int = 55) -> str:
    """Create a dependency-free SVG preview of one solved level."""
    grid = level.board.grid
    rows, cols = len(grid), len(grid[0])
    padding = 22
    width = cols * tile + 2 * padding
    height = rows * tile + 2 * padding
    result = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Generated word grid">',
        f'<rect width="{width}" height="{height}" fill="#f5f6fa" rx="16"/>',
    ]
    for r, row in enumerate(grid):
        for c, letter in enumerate(row):
            if letter is None:
                continue
            x = padding + c * tile + 2
            y = padding + r * tile + 2
            side = tile - 4
            result.append(f'<rect x="{x}" y="{y}" width="{side}" height="{side}" '
                          'rx="8" fill="#ffffff" stroke="#b9c6dc" stroke-width="2"/>')
            result.append(f'<text x="{x+side/2:.1f}" y="{y+side/2+7:.1f}" '
                          'text-anchor="middle" font-family="system-ui,sans-serif" '
                          f'font-weight="650" font-size="{tile*0.43:.1f}" '
                          f'fill="#243553">{escape(letter)}</text>')
    result.append('</svg>')
    return "\n".join(result) + "\n"
