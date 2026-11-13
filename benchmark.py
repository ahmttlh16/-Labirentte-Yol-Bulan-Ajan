"""Algoritmalari rastgele labirentler uzerinde karsilastiran konsol araci.

Arayuz acmadan calisir; bonus maddesi olan "kac kareye bakti" karsilastirmasini
tek seferde cok sayida labirent uzerinde olcer.

Kullanim:
    python benchmark.py                 # 100 labirent, 20x50
    python benchmark.py --runs 500      # daha fazla deneme
    python benchmark.py --rows 30 --cols 60 --density 0.3 --seed 7
"""

import argparse
import random
import time

import algorithms


class BenchNode:
    """Pygame'siz hafif dugum."""

    __slots__ = ("row", "col", "wall")

    def __init__(self, row, col, wall):
        self.row = row
        self.col = col
        self.wall = wall

    def get_pos(self):
        return self.row, self.col

    def is_wall(self):
        return self.wall


class BenchGrid:
    """Rastgele duvarlarla doldurulmus izgara."""

    def __init__(self, rows, cols, density, rng):
        self.rows = rows
        self.cols = cols
        self.nodes = [
            [BenchNode(r, c, rng.random() < density) for c in range(cols)]
            for r in range(rows)
        ]
        self.start = self.nodes[rows // 2][0]
        self.end = self.nodes[rows // 2][cols - 1]
        self.start.wall = False
        self.end.wall = False

    def get_node(self, row, col):
        return self.nodes[row][col]


def run(rows, cols, density, runs, seed):
    rng = random.Random(seed)
    keys = algorithms.COMPARISON_ORDER
    totals = {key: 0 for key in keys}
    durations = {key: 0.0 for key in keys}
    path_lengths = {key: 0 for key in keys}
    wins = {key: 0 for key in keys}
    solvable = 0
    mismatches = 0

    for _ in range(runs):
        grid = BenchGrid(rows, cols, density, rng)
        baseline = algorithms.bfs(grid, grid.start, grid.end)
        if not baseline.path:
            continue
        solvable += 1

        per_run = {}
        for key in keys:
            _, func = algorithms.ALGORITHMS[key]
            started = time.perf_counter()
            result = func(grid, grid.start, grid.end)
            durations[key] += time.perf_counter() - started
            totals[key] += result.examined
            path_lengths[key] += len(result.path)
            per_run[key] = result.examined
            if len(result.path) != len(baseline.path):
                mismatches += 1

        wins[min(per_run, key=per_run.get)] += 1

    if not solvable:
        print("Cozulebilir labirent uretilemedi; yogunlugu dusurmeyi dene.")
        return

    print()
    print("Labirent: {}x{}   yogunluk: {}   deneme: {}   cozulebilir: {}".format(
        rows, cols, density, runs, solvable
    ))
    print("-" * 78)
    print("{:<18} {:>12} {:>12} {:>12} {:>10}".format(
        "Algoritma", "ort. taranan", "ort. yol", "ort. sure(ms)", "en iyi"
    ))
    print("-" * 78)
    for key in keys:
        label, _ = algorithms.ALGORITHMS[key]
        print("{:<18} {:>12.1f} {:>12.1f} {:>12.3f} {:>10}".format(
            label,
            totals[key] / solvable,
            path_lengths[key] / solvable,
            durations[key] / solvable * 1000,
            wins[key],
        ))
    print("-" * 78)

    bfs_total = totals["bfs"]
    for key in keys:
        if key == "bfs":
            continue
        label, _ = algorithms.ALGORITHMS[key]
        saving = (1 - totals[key] / bfs_total) * 100 if bfs_total else 0.0
        print("{} BFS'e gore %{:.1f} daha az kareye bakti.".format(label, saving))

    print("Yol uzunlugu tutarsizligi: {}".format(mismatches))
    print()


def main():
    parser = argparse.ArgumentParser(description="BFS / A* / Hibrit karsilastirmasi")
    parser.add_argument("--rows", type=int, default=20)
    parser.add_argument("--cols", type=int, default=50)
    parser.add_argument("--density", type=float, default=0.25, help="duvar yogunlugu (0-1)")
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.rows, args.cols, args.density, args.runs, args.seed)


if __name__ == "__main__":
    main()
