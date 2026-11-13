"""Labirent veri modeli ve cizim katmani.

Grid, hucrelerden (Node) olusan bir izgaradir. Her hucrenin mantiksal bir
durumu (bos / duvar / baslangic / hedef) ve animasyon icin ayri bir "overlay"
rengi vardir. Overlay sadece gorsel oldugu icin temizlendiginde labirentin
kendisi bozulmaz.
"""

import random

import pygame

# --- Renk paleti -----------------------------------------------------------
WHITE = (248, 249, 250)
GRID_LINE = (214, 219, 223)
WALL_COLOR = (44, 62, 80)
START_COLOR = (39, 174, 96)
END_COLOR = (231, 76, 60)
VISITED_COLOR = (109, 180, 227)
PATH_COLOR = (241, 196, 15)

# --- Hucre durumlari -------------------------------------------------------
EMPTY = "empty"
WALL = "wall"
START = "start"
END = "end"


class Node:
    """Izgaradaki tek bir kare."""

    __slots__ = ("row", "col", "cell_size", "x", "y", "state", "color", "overlay")

    def __init__(self, row, col, cell_size):
        self.row = row
        self.col = col
        self.cell_size = cell_size
        self.x = col * cell_size
        self.y = row * cell_size
        self.state = EMPTY
        self.color = WHITE
        self.overlay = None

    def get_pos(self):
        return self.row, self.col

    def is_wall(self):
        return self.state == WALL

    def is_start(self):
        return self.state == START

    def is_end(self):
        return self.state == END

    def is_empty(self):
        return self.state == EMPTY

    def make_wall(self):
        self.state = WALL
        self.color = WALL_COLOR
        self.overlay = None

    def make_empty(self):
        self.state = EMPTY
        self.color = WHITE
        self.overlay = None

    def make_start(self):
        self.state = START
        self.color = START_COLOR
        self.overlay = None

    def make_end(self):
        self.state = END
        self.color = END_COLOR
        self.overlay = None

    # Animasyon katmani: baslangic/hedef/duvar hucrelerinin uzeri boyanmaz.
    def mark_visited(self):
        if self.state == EMPTY:
            self.overlay = VISITED_COLOR

    def mark_path(self):
        if self.state == EMPTY:
            self.overlay = PATH_COLOR

    def clear_overlay(self):
        self.overlay = None

    def draw(self, win):
        color = self.overlay if self.overlay is not None else self.color
        pygame.draw.rect(win, color, (self.x, self.y, self.cell_size, self.cell_size))

    def __repr__(self):
        return "Node({}, {}, {})".format(self.row, self.col, self.state)


class Grid:
    """Hucre matrisi, kullanici duzenlemeleri ve cizim."""

    def __init__(self, rows, cols, cell_size):
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.nodes = [
            [Node(row, col, cell_size) for col in range(cols)]
            for row in range(rows)
        ]

        self.start_pos = (rows // 2, 1)
        self.end_pos = (rows // 2, cols - 2)
        self.get_start().make_start()
        self.get_end().make_end()

    # --- Erisim ------------------------------------------------------------
    def get_node(self, row, col):
        return self.nodes[row][col]

    def get_start(self):
        return self.get_node(*self.start_pos)

    def get_end(self):
        return self.get_node(*self.end_pos)

    def get_node_from_mouse_pos(self, pos):
        """Fare konumunu hucreye cevirir; izgara disinda None doner."""
        x, y = pos
        col = x // self.cell_size
        row = y // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.get_node(row, col)
        return None

    # --- Duzenleme ---------------------------------------------------------
    def set_wall(self, node):
        if node.is_empty():
            node.make_wall()
            return True
        return False

    def clear_wall(self, node):
        if node.is_wall():
            node.make_empty()
            return True
        return False

    def set_start(self, node):
        """Baslangici tasir; hedefin uzerine tasinamaz."""
        if node.is_end():
            return False
        self.get_start().make_empty()
        node.make_start()
        self.start_pos = node.get_pos()
        return True

    def set_end(self, node):
        if node.is_start():
            return False
        self.get_end().make_empty()
        node.make_end()
        self.end_pos = node.get_pos()
        return True

    def clear_walls(self):
        """Tum duvarlari ve animasyon izlerini siler."""
        for row in self.nodes:
            for node in row:
                if node.is_wall():
                    node.make_empty()
                node.clear_overlay()

    def clear_overlays(self):
        """Sadece animasyon izlerini siler, labirent korunur."""
        for row in self.nodes:
            for node in row:
                node.clear_overlay()

    def count_walls(self):
        return sum(node.is_wall() for row in self.nodes for node in row)

    # --- Rastgele labirent -------------------------------------------------
    def generate_random_walls(self, density=0.28, attempts=40):
        """Dikey engel bloklarindan olusan, cozulebilir rastgele bir labirent uretir.

        Baslangic ve hedef hucreleri korunur. Uretilen labirentin cozulebilir
        oldugu BFS ile dogrulanir; cozulemezse yeniden denenir.
        """
        from algorithms import bfs  # dairesel import olmamasi icin yerel import

        protected = {self.start_pos, self.end_pos}
        for _ in range(attempts):
            self.clear_walls()
            wall_budget = int(self.rows * self.cols * density)
            placed = 0
            guard = 0
            while placed < wall_budget and guard < wall_budget * 20:
                guard += 1
                col = random.randrange(1, self.cols - 1)
                length = random.randint(3, max(4, self.rows // 2))
                top = random.randrange(0, max(1, self.rows - length + 1))
                gap = random.randrange(top, top + length)   # blokta bir gecit birak
                for row in range(top, min(self.rows, top + length)):
                    if row == gap or (row, col) in protected:
                        continue
                    if self.set_wall(self.get_node(row, col)):
                        placed += 1
            if bfs(self, self.get_start(), self.get_end()).path:
                return True

        # Hicbir deneme cozulebilir cikmadiysa bos labirente don.
        self.clear_walls()
        return False

    # --- Cizim -------------------------------------------------------------
    def draw(self, win):
        for row in self.nodes:
            for node in row:
                node.draw(win)
        self._draw_lines(win)

    def _draw_lines(self, win):
        width = self.cols * self.cell_size
        height = self.rows * self.cell_size
        for row in range(self.rows + 1):
            y = row * self.cell_size
            pygame.draw.line(win, GRID_LINE, (0, y), (width, y))
        for col in range(self.cols + 1):
            x = col * self.cell_size
            pygame.draw.line(win, GRID_LINE, (x, 0), (x, height))
