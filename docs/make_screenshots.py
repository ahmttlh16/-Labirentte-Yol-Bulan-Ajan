"""README icin ekran goruntulerini uretir (ekran/pencere gerektirmez).

Gercek arayuzun (main.App) kendi cizim kodunu kullanir: labirent, panel,
lejant ve karsilastirma tablosu uygulamada gorundugu gibi kaydedilir.
Ayni tohum (seed) kullanildigi icin ayni labirent her defasinda uretilir.

Kullanim (proje kokunden):

    python docs/make_screenshots.py
    python docs/make_screenshots.py --seed 7 --density 0.25
"""

import argparse
import os
import random
import sys

# pygame'i penceresiz (headless) baslat: import'tan ONCE ayarlanmali.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame  # noqa: E402  (headless ayarindan sonra import ediliyor)

import algorithms  # noqa: E402
from main import DEFAULT_SPEED, IDLE, App  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

# Animasyonu beklemeden tek hamlede bitirmek icin yuksek hiz.
DRAIN_SPEED = 10 ** 6


def save(app, filename):
    app.draw()
    path = os.path.join(OUTPUT_DIR, filename)
    pygame.image.save(app.win, path)
    print("kaydedildi: {}".format(os.path.relpath(path, PROJECT_ROOT)))


def drain(app):
    """Animasyon kuyruklarini bitirip son kareye gecer."""
    app.speed = DRAIN_SPEED
    guard = 0
    while app.state != IDLE and guard < 1000:
        app.advance_animation()
        guard += 1
    app.speed = DEFAULT_SPEED   # panelde gercek varsayilan hiz gorunsun


def main():
    parser = argparse.ArgumentParser(description="README gorsellerini uret")
    parser.add_argument("--seed", type=int, default=3, help="rastgele labirent tohumu")
    parser.add_argument("--density", type=float, default=0.15, help="duvar yogunlugu")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.seed(args.seed)

    app = App()
    if not app.grid.generate_random_walls(density=args.density):
        print("Cozulebilir labirent uretilemedi, baska bir --seed dene.", file=sys.stderr)
        return 1

    # 1) Arama oncesi: cizilmis labirent
    app.status = "Labirent hazir ({} duvar). SPACE ile aramayi baslat.".format(
        app.grid.count_walls()
    )
    save(app, "01-labirent.png")

    # 2-4) Her algoritmanin taramasi + buldugu yol
    files = {
        "hybrid": "02-hibrit.png",
        "astar": "03-astar.png",
        "bfs": "04-bfs.png",
    }
    for key in algorithms.COMPARISON_ORDER:
        app.stats.clear()                 # tek algoritmanin sonucu gorunsun
        app.run_algorithm(key)
        drain(app)
        save(app, files[key])

    # 5) K tusu: uc algoritma ayni labirentte, panelde karsilastirma tablosu
    app.compare_all()
    app.run_algorithm("hybrid")           # tablo dururken hibrit sonucu cizilir
    drain(app)
    app.status = "K: uc algoritma ayni labirentte karsilastirildi."
    save(app, "05-karsilastirma.png")

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
