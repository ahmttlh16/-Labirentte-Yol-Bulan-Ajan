"""Algoritma dogrulama testleri (pygame gerektirmez).

Calistirmak icin proje kokunden:
    python -m unittest discover -s tests -v
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algorithms  # noqa: E402


class FakeNode:
    """Algoritmalarin bekledigi en kucuk dugum arayuzu."""

    def __init__(self, row, col, wall=False):
        self.row = row
        self.col = col
        self.wall = wall

    def get_pos(self):
        return self.row, self.col

    def is_wall(self):
        return self.wall

    def __repr__(self):
        return "({}, {})".format(self.row, self.col)


class FakeGrid:
    """'#' duvar, '.' bos, 'S' baslangic, 'E' hedef."""

    def __init__(self, layout):
        rows = [line for line in layout.strip().splitlines()]
        self.rows = len(rows)
        self.cols = len(rows[0])
        self.nodes = []
        self.start = None
        self.end = None
        for r, line in enumerate(rows):
            row_nodes = []
            for c, char in enumerate(line):
                node = FakeNode(r, c, wall=(char == "#"))
                if char == "S":
                    self.start = node
                elif char == "E":
                    self.end = node
                row_nodes.append(node)
            self.nodes.append(row_nodes)

    def get_node(self, row, col):
        return self.nodes[row][col]

    @classmethod
    def random(cls, rows, cols, density, rng):
        chars = [
            ["#" if rng.random() < density else "." for _ in range(cols)]
            for _ in range(rows)
        ]
        chars[0][0] = "S"
        chars[rows - 1][cols - 1] = "E"
        return cls("\n".join("".join(row) for row in chars))


def is_valid_path(grid, path, start, end):
    """Yolun gercekten gecerli olup olmadigini dogrular."""
    if not path:
        return False
    if path[0] is not start or path[-1] is not end:
        return False
    for node in path:
        if node.is_wall():
            return False
    for prev, nxt in zip(path, path[1:]):
        (r1, c1), (r2, c2) = prev.get_pos(), nxt.get_pos()
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False
    return True


SIMPLE = """
S........
.######..
.......#.
######.#.
.........
....####.
........E
"""

NO_PATH = """
S...#....
....#....
....#....
....#...E
"""

ALL = (algorithms.bfs, algorithms.astar, algorithms.hybrid_bfs_astar)


class TestAlgorithms(unittest.TestCase):
    def test_simple_maze_paths_are_valid_and_equal_length(self):
        grid = FakeGrid(SIMPLE)
        lengths = []
        for func in ALL:
            result = func(grid, grid.start, grid.end)
            self.assertTrue(
                is_valid_path(grid, result.path, grid.start, grid.end),
                "{} gecersiz yol dondurdu".format(result.name),
            )
            lengths.append(len(result.path))
        self.assertEqual(len(set(lengths)), 1, "yol uzunluklari farkli: {}".format(lengths))

    def test_no_path_returns_empty(self):
        grid = FakeGrid(NO_PATH)
        for func in ALL:
            result = func(grid, grid.start, grid.end)
            self.assertEqual(result.path, [], "{} olmayan yolu buldu".format(result.name))
            self.assertGreater(result.examined, 0)

    def test_start_equals_end(self):
        grid = FakeGrid(SIMPLE)
        for func in ALL:
            result = func(grid, grid.start, grid.start)
            self.assertEqual(result.path, [grid.start])

    def test_random_mazes_optimality(self):
        """Hibrit ve A*, BFS'in buldugu en kisa yol uzunlugunu yakalamali."""
        rng = random.Random(1234)
        solvable = 0
        for _ in range(60):
            grid = FakeGrid.random(18, 30, 0.28, rng)
            baseline = algorithms.bfs(grid, grid.start, grid.end)
            if not baseline.path:
                continue
            solvable += 1
            for func in (algorithms.astar, algorithms.hybrid_bfs_astar):
                result = func(grid, grid.start, grid.end)
                self.assertTrue(
                    is_valid_path(grid, result.path, grid.start, grid.end),
                    "{} gecersiz yol dondurdu".format(result.name),
                )
                self.assertEqual(
                    len(result.path),
                    len(baseline.path),
                    "{} optimal degil: {} != {}".format(
                        result.name, len(result.path), len(baseline.path)
                    ),
                )
        self.assertGreater(solvable, 10, "yeterince cozulebilir labirent uretilmedi")

    def test_heuristic_search_examines_no_more_than_bfs_on_average(self):
        """Sezgisel aramalar ortalamada BFS'ten daha az kareye bakmali."""
        rng = random.Random(7)
        totals = {"BFS": 0, "A*": 0, "Hibrit (BFS+A*)": 0}
        for _ in range(40):
            grid = FakeGrid.random(18, 40, 0.22, rng)
            if not algorithms.bfs(grid, grid.start, grid.end).path:
                continue
            for func in ALL:
                result = func(grid, grid.start, grid.end)
                totals[result.name] += result.examined
        self.assertLess(totals["A*"], totals["BFS"])
        self.assertLess(totals["Hibrit (BFS+A*)"], totals["BFS"])


if __name__ == "__main__":
    unittest.main()
