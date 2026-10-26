"""Independent data checks for paper 5/6 answer authoring."""

import heapq
import itertools
from collections import deque


def topo_count():
    vertices = range(6)
    edges = [(0, 2), (0, 3), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
    return sum(
        all(p.index(u) < p.index(v) for u, v in edges)
        for p in itertools.permutations(vertices)
    )


def huffman(weights):
    q = list(weights)
    heapq.heapify(q)
    merged = []
    while len(q) > 1:
        a, b = heapq.heappop(q), heapq.heappop(q)
        merged.append(a + b)
        heapq.heappush(q, a + b)
    return merged, sum(merged)


def hash_insert(keys, m, step):
    table = [None] * m
    result = []
    for key in keys:
        start = key % m
        distance = step(key)
        for i in range(m):
            at = (start + i * distance) % m
            if table[at] is None:
                table[at] = key
                result.append((key, at, i + 1))
                break
        else:
            raise ValueError("full table")
    return table, result


def binary_tree(lo, hi, depth=1):
    if lo > hi:
        return []
    mid = (lo + hi) // 2
    return [(mid, depth)] + binary_tree(lo, mid - 1, depth + 1) + binary_tree(mid + 1, hi, depth + 1)


def stack_first_three():
    seen = set()

    def walk(next_push, stack, out):
        if next_push == 5 and not stack:
            if out[0] == 3:
                seen.add(tuple(out))
            return
        if next_push <= 4:
            walk(next_push + 1, stack + (next_push,), out)
        if stack:
            walk(next_push, stack[:-1], out + (stack[-1],))

    walk(1, (), ())
    return sorted(seen)


def aoe():
    edges = [(0, 1, 2), (0, 2, 3), (1, 3, 4), (2, 3, 1), (2, 4, 4), (3, 5, 3), (4, 5, 2), (1, 4, 1)]
    ve = [0] * 6
    for u in range(6):
        for a, b, w in edges:
            if a == u:
                ve[b] = max(ve[b], ve[u] + w)
    vl = [ve[5]] * 6
    for u in range(5, -1, -1):
        for a, b, w in edges:
            if a == u:
                vl[u] = min(vl[u], vl[b] - w)
    activity = [(u, v, ve[u], vl[v] - w) for u, v, w in edges]
    return ve, vl, activity


def shortest_graph():
    edges = [('A', 'B', 2), ('A', 'C', 3), ('B', 'C', 2), ('B', 'D', 5), ('C', 'D', 3), ('C', 'E', 6), ('D', 'E', 1)]
    adj = {x: [] for x in "ABCDE"}
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    dist = {x: float("inf") for x in adj}
    dist["A"] = 0
    q = [(0, "A")]
    while q:
        d, u = heapq.heappop(q)
        if d != dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(q, (dist[v], v))
    return dist


assert topo_count() == 16
assert huffman([2, 4, 7, 10, 15, 25]) == ([6, 13, 23, 38, 63], 143)
assert huffman([4, 7, 9, 10, 15, 25]) == ([11, 19, 26, 44, 70], 170)
assert huffman([3, 5, 7, 11, 13, 18]) == ([8, 15, 24, 33, 57], 137)
assert hash_insert([22, 1, 13, 11, 24, 35, 46], 11, lambda k: 1 + k % 10)[1] == [
    (22, 0, 1), (1, 1, 1), (13, 2, 1), (11, 4, 3), (24, 7, 2), (35, 8, 2), (46, 9, 2)
]
assert hash_insert([18, 29, 40, 7, 22, 35, 46], 11, lambda _: 1)[1] == [
    (18, 7, 1), (29, 8, 2), (40, 9, 3), (7, 10, 4), (22, 0, 1), (35, 2, 1), (46, 3, 2)
]
assert sum(depth for _, depth in binary_tree(1, 10)) == 29
assert sum(depth for _, depth in binary_tree(1, 11)) == 33
assert stack_first_three() == [(3, 2, 1, 4), (3, 2, 4, 1), (3, 4, 2, 1)]
assert shortest_graph() == {'A': 0, 'B': 2, 'C': 3, 'D': 6, 'E': 7}
assert aoe() == (
    [0, 2, 3, 6, 7, 9],
    [0, 2, 3, 6, 7, 9],
    [(0, 1, 0, 0), (0, 2, 0, 0), (1, 3, 2, 2), (2, 3, 3, 5),
     (2, 4, 3, 3), (3, 5, 6, 6), (4, 5, 7, 7), (1, 4, 2, 6)]
)
print("12 independent combinatorial, Huffman, search, stack, AOE and graph checks passed")
