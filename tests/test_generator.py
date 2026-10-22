"""Behavioral tests for generator and export formats."""

import json
import unittest
from xml.etree import ElementTree

from wordgrid import generate_board, generate_variants, layout_metrics, to_json, to_svg


class GeneratorTests(unittest.TestCase):
    def test_seed_reproducibility(self):
        a = generate_board(["CAT", "ART", "TAR"], 7, 7, seed=17)
        b = generate_board(["CAT", "ART", "TAR"], 7, 7, seed=17)
        self.assertIsNotNone(a)
        self.assertEqual(a.as_text(), b.as_text())
        self.assertEqual(a.placements, b.placements)

    def test_valid_turkish_example(self):
        board = generate_board(["AİLE", "ELA", "ARI"], 3, 4)
        self.assertIsNotNone(board)
        self.assertEqual(len(board.placements), 3)
        self.assertGreaterEqual(layout_metrics(board)["intersection_count"], 2)
        for placement in board.placements:
            for i, char in enumerate(placement.word):
                r = placement.row + (i if placement.orientation == "V" else 0)
                c = placement.col + (i if placement.orientation == "H" else 0)
                self.assertEqual(board.grid[r][c], char)

    def test_out_of_bounds_returns_no_solution(self):
        self.assertIsNone(generate_board(["LONGWORD"], 2, 3))

    def test_disconnected_layout_can_be_allowed(self):
        board = generate_board(["AB", "XY"], 2, 5, require_connected=False)
        self.assertIsNotNone(board)
        self.assertEqual(len(board.placements), 2)
        self.assertIsNone(generate_board(["AB", "XY"], 2, 5, require_connected=True))

    def test_duplicate_input_rejected(self):
        with self.assertRaises(ValueError):
            generate_board(["CAT", "CAT"], 8, 8)

    def test_invalid_length_rejected(self):
        with self.assertRaises(ValueError):
            generate_board(["A"], 4, 4)

    def test_deduplicated_variants(self):
        levels = generate_variants(["CAT", "ART", "TAR"], 7, 7, count=6, trials=12)
        signatures = {tuple(tuple(row) for row in l.board.grid) for l in levels}
        self.assertEqual(len(signatures), len(levels))
        self.assertLessEqual(len(levels), 6)

    def test_export_round_trip(self):
        levels = generate_variants(["AİLE", "ELA", "ARI"], 3, 4, count=1, trials=4)
        obj = json.loads(to_json(levels))
        self.assertEqual(obj["schema_version"], 1)
        self.assertEqual(obj["levels"][0]["rows"], 3)
        self.assertIn("İ", to_json(levels))
        svg = to_svg(levels[0])
        self.assertEqual(ElementTree.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")


if __name__ == "__main__":
    unittest.main()
