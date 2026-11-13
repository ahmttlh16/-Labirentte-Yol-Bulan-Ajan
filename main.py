"""Labirentte Yol Bulan Ajan - pygame arayuzu.

Kontroller
----------
Sol tik / surukle : duvar ciz          Sag tik / surukle : duvar sil
S + tik           : baslangici tasi    E + tik           : hedefi tasi
SPACE veya 1      : Hibrit (BFS+A*)    2 : A*             3 : BFS
K                 : uc algoritmayi karsilastir (animasyonsuz)
R                 : rastgele labirent  C : her seyi temizle   X : izleri temizle
+ / -             : animasyon hizi     ESC : cikis
"""

import sys

from collections import deque

import pygame

import algorithms
from grid_manager import (
    END_COLOR,
    PATH_COLOR,
    START_COLOR,
    VISITED_COLOR,
    WALL_COLOR,
    Grid,
)

# --- Labirent boyutu (odev sarti: en az 20x50) -----------------------------
ROWS = 20
COLS = 50
CELL_SIZE = 20

# --- Pencere ---------------------------------------------------------------
PANEL_HEIGHT = 116
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
WINDOW_WIDTH = GRID_WIDTH
WINDOW_HEIGHT = GRID_HEIGHT + PANEL_HEIGHT

FPS = 60
MIN_WALLS = 8                 # odev sarti: en az 8 engel
DEFAULT_SPEED = 4             # kare / frame
MIN_SPEED, MAX_SPEED = 1, 40

PANEL_BG = (28, 32, 38)
PANEL_TEXT = (236, 240, 241)
PANEL_MUTED = (149, 165, 166)
PANEL_ACCENT = (241, 196, 15)

# --- Durum makinesi --------------------------------------------------------
IDLE = "idle"
ANIMATING_VISITED = "animating_visited"
ANIMATING_PATH = "animating_path"

CONTROLS_LINE_1 = (
    "Sol tik: duvar  |  Sag tik: sil  |  S+tik: baslangic  |  E+tik: hedef  |  R: rastgele labirent"
)
CONTROLS_LINE_2 = (
    "SPACE/1: Hibrit (BFS+A*)  |  2: A*  |  3: BFS  |  K: karsilastir  |  "
    "C: temizle  |  X: izleri sil  |  +/-: hiz"
)

LEGEND = (
    ("Baslangic", START_COLOR),
    ("Hedef", END_COLOR),
    ("Duvar", WALL_COLOR),
    ("Taranan", VISITED_COLOR),
    ("Yol", PATH_COLOR),
)


class App:
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Labirentte Yol Bulan Ajan - BFS / A* / Hibrit")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 15)
        self.small_font = pygame.font.SysFont("consolas", 13)

        self.grid = Grid(ROWS, COLS, CELL_SIZE)
        self.state = IDLE
        self.speed = DEFAULT_SPEED

        self.visited_queue = deque()
        self.path_queue = deque()
        self.active_name = ""
        self.active_examined = 0
        self.active_path_len = 0

        # Karsilastirma tablosu: algoritma anahtari -> (etiket, taranan, yol)
        self.stats = {}
        self.status = "Duvar ciz (en az {}) ya da R ile rastgele labirent olustur.".format(MIN_WALLS)

    # -- yardimcilar --------------------------------------------------------
    @property
    def busy(self):
        return self.state != IDLE

    def _record(self, key, result):
        self.stats[key] = (
            result.name,
            result.examined,
            len(result.path),
        )

    def _enough_walls(self):
        walls = self.grid.count_walls()
        if walls >= MIN_WALLS:
            return True
        self.status = "En az {} duvar gerekli (su an {}). R ile rastgele labirent olusturabilirsin.".format(
            MIN_WALLS, walls
        )
        return False

    # -- aksiyonlar ---------------------------------------------------------
    def run_algorithm(self, key):
        """Tek algoritmayi calistirip animasyon kuyruklarini doldurur."""
        if not self._enough_walls():
            return

        label, func = algorithms.ALGORITHMS[key]
        self.grid.clear_overlays()
        result = func(self.grid, self.grid.get_start(), self.grid.get_end())
        self._record(key, result)

        self.visited_queue = deque(result.visited_order)
        self.path_queue = deque(result.path)
        self.active_name = label
        self.active_examined = result.examined
        self.active_path_len = len(result.path)
        self.state = ANIMATING_VISITED
        self.status = "{} araniyor...".format(label)

    def compare_all(self):
        """Uc algoritmayi animasyonsuz calistirip taranan kare sayilarini karsilastirir."""
        if not self._enough_walls():
            return

        self.grid.clear_overlays()
        start, end = self.grid.get_start(), self.grid.get_end()
        print("\n--- Karsilastirma ({} duvar) ---".format(self.grid.count_walls()))
        for key in algorithms.COMPARISON_ORDER:
            label, func = algorithms.ALGORITHMS[key]
            result = func(self.grid, start, end)
            self._record(key, result)
            print(
                "{:<18} taranan kare: {:>5}   yol uzunlugu: {:>4}".format(
                    label,
                    result.examined,
                    len(result.path) if result.path else 0,
                )
            )

        best = min(
            (data for data in self.stats.values() if data[2]),
            key=lambda data: data[1],
            default=None,
        )
        if best is None:
            self.status = "Karsilastirma tamam: hicbir algoritma yol bulamadi."
        else:
            self.status = "Karsilastirma tamam. En az kareye bakan: {} ({} kare).".format(
                best[0], best[1]
            )

    def reset(self, walls_too):
        self.visited_queue.clear()
        self.path_queue.clear()
        self.state = IDLE
        self.stats.clear()
        if walls_too:
            self.grid.clear_walls()
            self.status = "Labirent temizlendi."
        else:
            self.grid.clear_overlays()
            self.status = "Arama izleri silindi, labirent korundu."

    def random_maze(self):
        ok = self.grid.generate_random_walls()
        self.reset(walls_too=False)
        self.status = (
            "Rastgele labirent olusturuldu ({} duvar).".format(self.grid.count_walls())
            if ok
            else "Cozulebilir rastgele labirent uretilemedi, tekrar dene (R)."
        )

    # -- olaylar ------------------------------------------------------------
    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            return False
        if key == pygame.K_c:
            self.reset(walls_too=True)
        elif key == pygame.K_x:
            self.reset(walls_too=False)
        elif key == pygame.K_r and not self.busy:
            self.random_maze()
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.speed = min(MAX_SPEED, self.speed + 1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed = max(MIN_SPEED, self.speed - 1)
        elif not self.busy:
            if key in (pygame.K_SPACE, pygame.K_1, pygame.K_KP1):
                self.run_algorithm("hybrid")
            elif key in (pygame.K_2, pygame.K_KP2):
                self.run_algorithm("astar")
            elif key in (pygame.K_3, pygame.K_KP3):
                self.run_algorithm("bfs")
            elif key == pygame.K_k:
                self.compare_all()
        return True

    def handle_mouse(self):
        """Fare basili tutuldugu surece duvar ciz / sil (surukleme destegi)."""
        if self.busy:
            return
        left, _, right = pygame.mouse.get_pressed()
        if not (left or right):
            return

        node = self.grid.get_node_from_mouse_pos(pygame.mouse.get_pos())
        if node is None:
            return

        keys = pygame.key.get_pressed()
        if left and keys[pygame.K_s]:
            if self.grid.set_start(node):
                self.grid.clear_overlays()
                self.status = "Baslangic tasindi: {}".format(node.get_pos())
        elif left and keys[pygame.K_e]:
            if self.grid.set_end(node):
                self.grid.clear_overlays()
                self.status = "Hedef tasindi: {}".format(node.get_pos())
        elif left:
            self.grid.set_wall(node)
        elif right:
            self.grid.clear_wall(node)

    # -- animasyon ----------------------------------------------------------
    def advance_animation(self):
        if self.state == ANIMATING_VISITED:
            for _ in range(self.speed):
                if self.visited_queue:
                    self.visited_queue.popleft().mark_visited()
                    continue
                if self.path_queue:
                    self.state = ANIMATING_PATH
                    self.status = "{}: yol bulundu, ciziliyor...".format(self.active_name)
                else:
                    self.state = IDLE
                    self.status = "{}: {} kare tarandi, yol YOK.".format(
                        self.active_name, self.active_examined
                    )
                    print("{}: {} kare tarandi. Yol bulunamadi.".format(
                        self.active_name, self.active_examined
                    ))
                break

        elif self.state == ANIMATING_PATH:
            for _ in range(self.speed):
                if self.path_queue:
                    self.path_queue.popleft().mark_path()
                    continue
                self.state = IDLE
                self.status = "{}: {} kare tarandi, en kisa yol {} adim.".format(
                    self.active_name, self.active_examined, self.active_path_len
                )
                print("{}: {} kare tarandi. En kisa yol: {} adim.".format(
                    self.active_name, self.active_examined, self.active_path_len
                ))
                break

    # -- cizim --------------------------------------------------------------
    def draw_panel(self):
        top = GRID_HEIGHT
        pygame.draw.rect(self.win, PANEL_BG, (0, top, WINDOW_WIDTH, PANEL_HEIGHT))

        # Lejant
        x = 10
        y = top + 8
        for label, color in LEGEND:
            pygame.draw.rect(self.win, color, (x, y, 12, 12))
            pygame.draw.rect(self.win, PANEL_MUTED, (x, y, 12, 12), 1)
            surface = self.small_font.render(label, True, PANEL_TEXT)
            self.win.blit(surface, (x + 17, y - 1))
            x += 22 + surface.get_width() + 14

        info = "duvar: {}   hiz: {}".format(self.grid.count_walls(), self.speed)
        info_surface = self.small_font.render(info, True, PANEL_MUTED)
        self.win.blit(info_surface, (WINDOW_WIDTH - info_surface.get_width() - 10, y - 1))

        # Kontroller
        self.win.blit(self.small_font.render(CONTROLS_LINE_1, True, PANEL_MUTED), (10, top + 28))
        self.win.blit(self.small_font.render(CONTROLS_LINE_2, True, PANEL_MUTED), (10, top + 45))

        # Durum satiri
        self.win.blit(self.font.render(self.status, True, PANEL_ACCENT), (10, top + 66))

        # Karsilastirma tablosu
        if self.stats:
            parts = []
            for key in algorithms.COMPARISON_ORDER:
                if key not in self.stats:
                    continue
                label, examined, path_len = self.stats[key]
                parts.append(
                    "{}: {} kare / {} adim".format(label, examined, path_len if path_len else "-")
                )
            line = "   |   ".join(parts)
            self.win.blit(self.font.render(line, True, PANEL_TEXT), (10, top + 90))
        else:
            hint = "Karsilastirma icin K'ya bas (uc algoritma da ayni labirentte calisir)."
            self.win.blit(self.small_font.render(hint, True, PANEL_MUTED), (10, top + 92))

    def draw(self):
        self.grid.draw(self.win)
        self.draw_panel()
        pygame.display.update()

    # -- ana dongu ----------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.handle_key(event.key)

            self.handle_mouse()
            self.advance_animation()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    try:
        App().run()
    except pygame.error as exc:
        print("pygame hatasi: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
