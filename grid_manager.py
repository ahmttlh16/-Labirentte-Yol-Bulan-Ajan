import pygame

WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
BLACK = (44, 62, 80)
GREEN = (39, 174, 96)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
YELLOW = (241, 196, 15)

EMPTY = "empty"
WALL = "wall"
START = "start"
END = "end"


class Node:
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
        self.color = BLACK
        self.overlay = None

    def make_empty(self):
        self.state = EMPTY
        self.color = WHITE
        self.overlay = None

    def make_start(self):
        self.state = START
        self.color = GREEN

    def make_end(self):
        self.state = END
        self.color = RED

    def mark_visited(self):
        if self.state == EMPTY:
            self.overlay = BLUE

    def mark_path(self):
        if self.state == EMPTY:
            self.overlay = YELLOW

    def clear_overlay(self):
        self.overlay = None

    def draw(self, win):
        color = self.overlay if self.overlay is not None else self.color
        rect = (self.x, self.y, self.cell_size, self.cell_size)
        pygame.draw.rect(win, color, rect)


class Grid:
    def __init__(self, rows, cols, cell_size):
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.nodes = [
            [Node(row, col, cell_size) for col in range(cols)]
            for row in range(rows)
        ]

        self.start_pos = (rows // 2, 2)
        self.end_pos = (rows // 2, cols - 3)
        self._place_start_and_end()

    def _place_start_and_end(self):
        start_row, start_col = self.start_pos
        end_row, end_col = self.end_pos
        self.get_node(start_row, start_col).make_start()
        self.get_node(end_row, end_col).make_end()

    def get_node(self, row, col):
        return self.nodes[row][col]

    def get_node_from_mouse_pos(self, pos):
        x, y = pos
        col = x // self.cell_size
        row = y // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.get_node(row, col)
        return None

    def set_wall(self, node):
        if node.is_empty():
            node.make_wall()

    def clear_wall(self, node):
        if node.is_wall():
            node.make_empty()

    def reset_walls(self):
        for row in self.nodes:
            for node in row:
                if node.is_wall():
                    node.make_empty()
                node.clear_overlay()
        self._place_start_and_end()

    def clear_overlays(self):
        for row in self.nodes:
            for node in row:
                node.clear_overlay()

    def count_walls(self):
        return sum(node.is_wall() for row in self.nodes for node in row)

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
            pygame.draw.line(win, GRAY, (0, y), (width, y))

        for col in range(self.cols + 1):
            x = col * self.cell_size
            pygame.draw.line(win, GRAY, (x, 0), (x, height))
