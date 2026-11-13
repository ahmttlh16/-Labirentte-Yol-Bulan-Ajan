"""Labirent uzerinde calisan arama algoritmalari.

Bu modul kasitli olarak pygame'den bagimsizdir; sadece asagidaki kucuk
arayuzu bekler:

    grid.rows, grid.cols      -> int
    grid.get_node(row, col)   -> node
    node.get_pos()            -> (row, col)
    node.is_wall()            -> bool

Bu sayede algoritmalar arayuz olmadan da test edilebilir.
"""

import heapq
from collections import deque, namedtuple

# Arama sonucu: tarama sirasi (animasyon icin), bulunan yol ve istatistik.
SearchResult = namedtuple("SearchResult", "name visited_order path examined")

INF = float("inf")

# 4 yonlu hareket (yukari, asagi, sol, sag).
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _neighbors(grid, node):
    """Dugumun duvar olmayan komsularini dondurur."""
    result = []
    row, col = node.get_pos()
    for d_row, d_col in DIRECTIONS:
        n_row, n_col = row + d_row, col + d_col
        if 0 <= n_row < grid.rows and 0 <= n_col < grid.cols:
            neighbor = grid.get_node(n_row, n_col)
            if not neighbor.is_wall():
                result.append(neighbor)
    return result


def _manhattan(node_a, node_b):
    """4 yonlu birim maliyetli grid icin tutarli (consistent) sezgisel."""
    row_a, col_a = node_a.get_pos()
    row_b, col_b = node_b.get_pos()
    return abs(row_a - row_b) + abs(col_a - col_b)


def _walk_to_root(parents, root, node):
    """node -> root yonunde ebeveyn zincirini takip ederek liste olusturur."""
    path = [node]
    while node is not root:
        node = parents[node]
        path.append(node)
    return path


# ---------------------------------------------------------------------------
# 1) Klasik BFS - referans (baseline) algoritma
# ---------------------------------------------------------------------------
def bfs(grid, start, end):
    """Genislik oncelikli arama. Birim maliyetli gridde en kisa yolu garanti eder."""
    visited_order = []
    if start is end:
        return SearchResult("BFS", visited_order, [start], 0)

    parents = {}
    visited = {start}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        visited_order.append(current)

        if current is end:
            path = _walk_to_root(parents, start, current)
            path.reverse()
            return SearchResult("BFS", visited_order, path, len(visited_order))

        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parents[neighbor] = current
            queue.append(neighbor)

    return SearchResult("BFS", visited_order, [], len(visited_order))


# ---------------------------------------------------------------------------
# 2) A* - sezgisel arama (bonus madde)
# ---------------------------------------------------------------------------
def astar(grid, start, end):
    """Manhattan sezgiseli ile A*. Sezgisel tutarli oldugu icin yol optimaldir."""
    visited_order = []
    came_from = {}

    g_score = {start: 0}
    counter = 0
    open_heap = [(_manhattan(start, end), counter, start)]
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        visited_order.append(current)

        if current is end:
            path = _walk_to_root(came_from, start, current)
            path.reverse()
            return SearchResult("A*", visited_order, path, len(visited_order))

        for neighbor in _neighbors(grid, current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, INF):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                counter += 1
                heapq.heappush(
                    open_heap,
                    (tentative_g + _manhattan(neighbor, end), counter, neighbor),
                )

    return SearchResult("A*", visited_order, [], len(visited_order))


# ---------------------------------------------------------------------------
# 3) Hibrit yontem: basi BFS, sonu A* olan cift yonlu arama
# ---------------------------------------------------------------------------
def hybrid_bfs_astar(grid, start, end):
    """BFS + A* hibrit cift yonlu arama.

    - Ileri cephe baslangictan BFS ile katman katman buyur (sezgisel kullanmaz),
      bu yuzden kuyrugunun basi her zaman o anki katman derinligini (min g) verir.
    - Geri cephe hedeften A* ile baslangica dogru sezgisel guduyle ilerler.
    - Cepheler dengeli buyusun diye her adimda derinligi (min g) kucuk olan
      taraf genisletilir.
    - Durma kosulu iki alt sinirin en buyugudur:
        1) ileri cephenin min g'si + geri cephenin min g'si   (cift yonlu sinir)
        2) geri cephenin min f'si                             (A* siniri)
      Her ikisi de gercek en kisa mesafenin alt siniri oldugu icin maksimumu da
      alt sinirdir; bulunan en iyi toplam bu siniri gecmedigi anda arama
      guvenle durdurulabilir. Bu sayede hem en kisa yol garanti edilir hem de
      cift yonlu aramalarda sik yapilan "ilk karsilasmada dur" hatasindan
      (1 adim uzun yol) kacinilir.
    """
    name = "Hibrit (BFS+A*)"
    visited_order = []
    if start is end:
        return SearchResult(name, visited_order, [start], 0)

    # Ileri taraf: BFS
    g_fwd = {start: 0}
    parent_fwd = {}
    frontier_fwd = deque([start])
    closed_fwd = set()

    # Geri taraf: A* (f = g + h(n, start))
    g_bwd = {end: 0}
    parent_bwd = {}
    counter = 0
    start_h = _manhattan(end, start)
    open_bwd = [(start_h, 0, counter, end)]   # (f, g, sira, dugum) - f'ye gore sirali
    g_order_bwd = [(0, counter, end)]         # (g, sira, dugum)    - g'ye gore sirali
    closed_bwd = set()

    best_total = INF

    def _stale(node, entry_g):
        """Heap'teki kayit guncelligini yitirmis mi?"""
        return node in closed_bwd or entry_g > g_bwd.get(node, INF)

    while frontier_fwd and open_bwd:
        # Cephelerin basindaki bayat kayitlari at.
        while frontier_fwd and frontier_fwd[0] in closed_fwd:
            frontier_fwd.popleft()
        while open_bwd and _stale(open_bwd[0][3], open_bwd[0][1]):
            heapq.heappop(open_bwd)
        while g_order_bwd and _stale(g_order_bwd[0][2], g_order_bwd[0][0]):
            heapq.heappop(g_order_bwd)
        if not frontier_fwd or not open_bwd or not g_order_bwd:
            break

        min_g_fwd = g_fwd[frontier_fwd[0]]
        min_g_bwd = g_order_bwd[0][0]
        min_f_bwd = open_bwd[0][0]

        lower_bound = max(min_g_fwd + min_g_bwd, min_f_bwd)
        if best_total <= lower_bound:
            break   # daha kisasi mumkun degil

        if min_g_fwd <= min_g_bwd:
            # --- BFS adimi ---
            current = frontier_fwd.popleft()
            if current in closed_fwd:
                continue
            closed_fwd.add(current)
            visited_order.append(current)

            for neighbor in _neighbors(grid, current):
                tentative = g_fwd[current] + 1
                if tentative < g_fwd.get(neighbor, INF):
                    g_fwd[neighbor] = tentative
                    parent_fwd[neighbor] = current
                    frontier_fwd.append(neighbor)
                    if neighbor in g_bwd:
                        best_total = min(best_total, tentative + g_bwd[neighbor])
        else:
            # --- A* adimi ---
            _, _, _, current = heapq.heappop(open_bwd)
            if current in closed_bwd:
                continue
            closed_bwd.add(current)
            visited_order.append(current)

            for neighbor in _neighbors(grid, current):
                tentative = g_bwd[current] + 1
                if tentative < g_bwd.get(neighbor, INF):
                    g_bwd[neighbor] = tentative
                    parent_bwd[neighbor] = current
                    counter += 1
                    heapq.heappush(
                        open_bwd,
                        (
                            tentative + _manhattan(neighbor, start),
                            tentative,
                            counter,
                            neighbor,
                        ),
                    )
                    heapq.heappush(g_order_bwd, (tentative, counter, neighbor))
                    if neighbor in g_fwd:
                        best_total = min(best_total, g_fwd[neighbor] + tentative)

    # Iki cephenin kesistigi en iyi bulusma noktasini sec.
    meeting = None
    best = INF
    for node, cost_bwd in g_bwd.items():
        cost_fwd = g_fwd.get(node)
        if cost_fwd is not None and cost_fwd + cost_bwd < best:
            best = cost_fwd + cost_bwd
            meeting = node

    if meeting is None:
        return SearchResult(name, visited_order, [], len(visited_order))

    head = _walk_to_root(parent_fwd, start, meeting)
    head.reverse()
    tail = _walk_to_root(parent_bwd, end, meeting)
    path = head + tail[1:]
    return SearchResult(name, visited_order, path, len(visited_order))


# Arayuzun kullandigi kayit: anahtar -> (etiket, fonksiyon)
ALGORITHMS = {
    "hybrid": ("Hibrit (BFS+A*)", hybrid_bfs_astar),
    "astar": ("A*", astar),
    "bfs": ("BFS", bfs),
}

# Karsilastirma tablosundaki sira.
COMPARISON_ORDER = ("hybrid", "astar", "bfs")
