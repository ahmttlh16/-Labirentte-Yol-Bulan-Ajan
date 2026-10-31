from collections import deque

import pygame

import algorithms
from grid_manager import Grid

ROWS = 20
COLS = 50
CELL_SIZE = 20
STATUS_HEIGHT = 32

WINDOW_WIDTH = COLS * CELL_SIZE
WINDOW_HEIGHT = ROWS * CELL_SIZE + STATUS_HEIGHT

FPS = 60
MIN_WALLS = 8
NODES_PER_FRAME = 3

STATUS_BG = (30, 30, 30)
STATUS_TEXT_COLOR = (255, 255, 255)
IDLE_HINT = "SPACE: A*  |  ENTER: Bidirectional BFS  |  C: Temizle  |  Sol tik: duvar, Sag tik: sil"

IDLE = "idle"
ANIMATING_VISITED = "animating_visited"
ANIMATING_PATH = "animating_path"


def draw_status_bar(win, font, message):
    bar_rect = (0, ROWS * CELL_SIZE, WINDOW_WIDTH, STATUS_HEIGHT)
    pygame.draw.rect(win, STATUS_BG, bar_rect)
    text_surface = font.render(message, True, STATUS_TEXT_COLOR)
    win.blit(text_surface, (8, ROWS * CELL_SIZE + 6))


def start_search(grid, key):
    start = grid.get_node(*grid.start_pos)
    end = grid.get_node(*grid.end_pos)

    if key == pygame.K_SPACE:
        visited, path = algorithms.astar(grid, start, end)
    else:
        visited, path = algorithms.bidirectional_bfs(grid, start, end)

    return deque(visited), deque(path)


def main():
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Labirentte Yol Bulan Ajan")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    grid = Grid(ROWS, COLS, CELL_SIZE)

    state = IDLE
    visited_queue = deque()
    path_queue = deque()
    status_message = IDLE_HINT
    current_algo_name = ""
    total_visited = 0
    total_path = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    grid.reset_walls()
                    visited_queue.clear()
                    path_queue.clear()
                    state = IDLE
                    status_message = IDLE_HINT
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) and state == IDLE:
                    wall_count = grid.count_walls()
                    if wall_count >= MIN_WALLS:
                        grid.clear_overlays()
                        visited_queue, path_queue = start_search(grid, event.key)
                        total_visited = len(visited_queue)
                        total_path = len(path_queue)
                        state = ANIMATING_VISITED
                        current_algo_name = "A*" if event.key == pygame.K_SPACE else "Bidirectional BFS"
                        status_message = f"{current_algo_name} araniyor..."
                    else:
                        status_message = (
                            f"En az {MIN_WALLS} duvar cizmelisin! (Su anki: {wall_count})"
                        )

        if state == IDLE:
            left_pressed, _, right_pressed = pygame.mouse.get_pressed()
            if left_pressed or right_pressed:
                node = grid.get_node_from_mouse_pos(pygame.mouse.get_pos())
                if node is not None:
                    if left_pressed:
                        grid.set_wall(node)
                    elif right_pressed:
                        grid.clear_wall(node)

        elif state == ANIMATING_VISITED:
            for _ in range(NODES_PER_FRAME):
                if not visited_queue:
                    if path_queue:
                        state = ANIMATING_PATH
                        status_message = "Yol bulundu! Ciziliyor..."
                    else:
                        state = IDLE
                        status_message = f"{current_algo_name}: {total_visited} kare tarandi. Yol bulunamadi!"
                        print(f"{current_algo_name} Algoritmasi {total_visited} kare taradi. Yol bulunamadi.")
                    break
                visited_queue.popleft().mark_visited()

        elif state == ANIMATING_PATH:
            for _ in range(NODES_PER_FRAME):
                if not path_queue:
                    state = IDLE
                    status_message = (
                        f"{current_algo_name}: {total_visited} kare tarandi, "
                        f"en kisa yol {total_path} adim. (C: temizle)"
                    )
                    print(
                        f"{current_algo_name} Algoritmasi {total_visited} kare taradi. "
                        f"En kisa yol uzunlugu: {total_path} adim."
                    )
                    break
                path_queue.popleft().mark_path()

        grid.draw(win)
        draw_status_bar(win, font, status_message)
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
