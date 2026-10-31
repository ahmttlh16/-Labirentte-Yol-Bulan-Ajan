import heapq
from collections import deque


def _get_neighbors(grid, node):
    neighbors = []
    row, col = node.get_pos()
    for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        n_row, n_col = row + d_row, col + d_col
        if 0 <= n_row < grid.rows and 0 <= n_col < grid.cols:
            neighbor = grid.get_node(n_row, n_col)
            if not neighbor.is_wall():
                neighbors.append(neighbor)
    return neighbors


def _manhattan_distance(node_a, node_b):
    row_a, col_a = node_a.get_pos()
    row_b, col_b = node_b.get_pos()
    return abs(row_a - row_b) + abs(col_a - col_b)


def _reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def astar(grid, start, end):
    visited_order = []
    came_from = {}

    g_score = {start: 0}
    f_score = {start: _manhattan_distance(start, end)}

    counter = 0
    open_set = [(f_score[start], counter, start)]
    open_set_hash = {start}

    while open_set:
        _, _, current = heapq.heappop(open_set)
        open_set_hash.discard(current)

        if current == end:
            return visited_order, _reconstruct_path(came_from, current)

        visited_order.append(current)

        for neighbor in _get_neighbors(grid, current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + _manhattan_distance(neighbor, end)
                if neighbor not in open_set_hash:
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                    open_set_hash.add(neighbor)

    return visited_order, []


def _expand_layer(grid, queue, visited_this_side, visited_other_side, predecessors_this_side, visited_order):
    meeting_node = None
    for _ in range(len(queue)):
        current = queue.popleft()
        visited_order.append(current)

        for neighbor in _get_neighbors(grid, current):
            if neighbor in visited_this_side:
                continue
            visited_this_side.add(neighbor)
            predecessors_this_side[neighbor] = current
            queue.append(neighbor)

            if meeting_node is None and neighbor in visited_other_side:
                meeting_node = neighbor

    return meeting_node


def _build_path_to_root(predecessors, root, node):
    path = [node]
    while node != root:
        node = predecessors[node]
        path.append(node)
    return path


def bidirectional_bfs(grid, start, end):
    visited_order = []

    if start == end:
        return visited_order, [start]

    visited_start = {start}
    visited_end = {end}
    predecessors_start = {}
    predecessors_end = {}

    queue_start = deque([start])
    queue_end = deque([end])

    meeting_node = None
    while queue_start and queue_end and meeting_node is None:
        meeting_node = _expand_layer(
            grid, queue_start, visited_start, visited_end, predecessors_start, visited_order
        )
        if meeting_node is None:
            meeting_node = _expand_layer(
                grid, queue_end, visited_end, visited_start, predecessors_end, visited_order
            )

    if meeting_node is None:
        return visited_order, []

    path_from_start = _build_path_to_root(predecessors_start, start, meeting_node)
    path_from_start.reverse()

    path_from_end = _build_path_to_root(predecessors_end, end, meeting_node)

    full_path = path_from_start + path_from_end[1:]
    return visited_order, full_path
