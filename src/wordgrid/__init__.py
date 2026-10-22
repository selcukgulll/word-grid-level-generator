"""Procedural word-grid level generation using constrained search."""

from .generator import BoardResult, Placement, generate_board
from .levels import LevelVariant, generate_variants, layout_metrics, to_json, to_svg

__all__ = [
    "BoardResult", "Placement", "LevelVariant", "generate_board",
    "generate_variants", "layout_metrics", "to_json", "to_svg",
]
