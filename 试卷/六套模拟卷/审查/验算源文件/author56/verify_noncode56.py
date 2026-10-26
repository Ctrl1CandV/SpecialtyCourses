"""Independent checks for the non-code answers in papers 5 and 6."""

from collections import deque

from compute56 import aoe, binary_tree, hash_insert, huffman, shortest_graph, stack_first_three, topo_count


class Node:
    def __init__(self, key):
        self.key, self.left, self.right, self.height = key, None, None, 1


def h(p):
    return p.height if p else 0


def update(p):
    p.height = max(h(p.left), h(p.right)) + 1
    return p


def rotate_left(p):
    q = p.right
    p.right = q.left
    q.left = p
    update(p)
    return update(q)


def rotate_right(p):
    q = p.left
    p.left = q.right
    q.right = p
    update(p)
    return update(q)


def avl_insert(p, key):
    if p is None:
        return Node(key)
    if key < p.key:
        p.left = avl_insert(p.left, key)
    else:
        p.right = avl_insert(p.right, key)
    update(p)
    balance = h(p.left) - h(p.right)
    if balance > 1:
        if key > p.left.key:
            p.left = rotate_left(p.left)
        return rotate_right(p)
    if balance < -1:
        if key < p.right.key:
            p.right = rotate_right(p.right)
        return rotate_left(p)
    return p


def bst_insert(p, key):
    if p is None:
        return Node(key)
    if key < p.key:
        p.left = bst_insert(p.left, key)
    else:
        p.right = bst_insert(p.right, key)
    return p


def children(p):
    return None if p is None else (p.key, children(p.left), children(p.right))


def depth_sum(p, level=1):
    return 0 if p is None else level + depth_sum(p.left, level + 1) + depth_sum(p.right, level + 1)


def postorder(p):
    return [] if p is None else postorder(p.left) + postorder(p.right) + [p.key]


def build_from_pre_in(pre, ino):
    if not pre:
        return None
    p = Node(pre[0])
    cut = ino.index(pre[0])
    p.left = build_from_pre_in(pre[1:cut + 1], ino[:cut])
    p.right = build_from_pre_in(pre[cut + 1:], ino[cut + 1:])
    return p


tree = build_from_pre_in(list("ABDECFG"), list("DBEAFCG"))
assert children(tree) == (
    "A", ("B", ("D", None, None), ("E", None, None)),
    ("C", ("F", None, None), ("G", None, None)),
)
assert postorder(tree) == list("DEBFGCA")
assert list("DBEAFCG").index("D") == 0
assert list("DBEAFCG").index("F") == 4

root = None
for x in [40, 20, 10, 30, 60, 50, 70]:
    root = bst_insert(root, x)
assert children(root) == (
    40, (20, (10, None, None), (30, None, None)),
    (60, (50, None, None), (70, None, None)),
)
assert postorder(root) == [10, 30, 20, 50, 70, 60, 40]
assert depth_sum(root) == 17

ordinary = balanced = None
for x in [30, 10, 20, 50, 40, 60, 70]:
    ordinary = bst_insert(ordinary, x)
    balanced = avl_insert(balanced, x)
assert depth_sum(ordinary) == 18
assert children(balanced) == (
    40, (20, (10, None, None), (30, None, None)),
    (60, (50, None, None), (70, None, None)),
)
assert depth_sum(balanced) == 17

graph = {
    0: [1, 2], 1: [0, 2], 2: [0, 1],
    3: [4], 4: [3, 5], 5: [4], 6: [],
}
dfs_seen, dfs_order, dfs_edges = set(), [], []


def dfs(u):
    dfs_seen.add(u)
    dfs_order.append(u)
    for v in graph[u]:
        if v not in dfs_seen:
            dfs_edges.append((u, v))
            dfs(v)


for u in graph:
    if u not in dfs_seen:
        dfs(u)
bfs_seen, bfs_order, bfs_edges = set(), [], []
for start in graph:
    if start in bfs_seen:
        continue
    bfs_seen.add(start)
    q = deque([start])
    while q:
        u = q.popleft()
        bfs_order.append(u)
        for v in graph[u]:
            if v not in bfs_seen:
                bfs_seen.add(v)
                bfs_edges.append((u, v))
                q.append(v)
assert dfs_order == bfs_order == list(range(7))
assert dfs_edges == [(0, 1), (1, 2), (3, 4), (4, 5)]
assert bfs_edges == [(0, 1), (0, 2), (3, 4), (4, 5)]

records = [('a', 'C', 2), ('b', 'A', 1), ('c', 'B', 2), ('d', 'A', 2), ('e', 'B', 1), ('f', 'A', 1)]
second_first = sorted(records, key=lambda x: x[2])
main_second = sorted(second_first, key=lambda x: x[1])
main_first = sorted(records, key=lambda x: x[1])
second_second = sorted(main_first, key=lambda x: x[2])
assert ''.join(x[0] for x in second_first) == 'befacd'
assert ''.join(x[0] for x in main_second) == 'bfdeca'
assert ''.join(x[0] for x in second_second) == 'bfedca'

original, after = huffman([2, 4, 7, 10, 15, 25]), huffman([4, 7, 9, 10, 15, 25])
assert original[1] == 143 and after[1] == 170 and 143 + 7*5 == 178
assert topo_count() == 16
assert binary_tree(1, 10)[0][0] == 5
assert sum(d for _, d in binary_tree(1, 10)) == 29
assert len(stack_first_three()) == 3
assert max(
    n for n in range(1, 32)
    if sum(i <= n and 2*i > n for i in range(8, 16)) == 2
) == 27

assert huffman([3, 5, 7, 11, 13, 18]) == ([8, 15, 24, 33, 57], 137)
assert sum(d for _, d in binary_tree(1, 11)) == 33
assert aoe()[0] == aoe()[1] == [0, 2, 3, 6, 7, 9]
assert shortest_graph() == {'A': 0, 'B': 2, 'C': 3, 'D': 6, 'E': 7}
assert sum(t for _, _, t in hash_insert([18, 29, 40, 7, 22, 35, 46], 11, lambda _: 1)[1]) == 14

pattern = 'abcabca'
next_values = [0]
for j in range(2, len(pattern) + 1):
    prefix = pattern[:j-1]
    lengths = [k for k in range(1, len(prefix))
               if prefix[:k] == prefix[-k:]]
    next_values.append((max(lengths) if lengths else 0) + 1)
assert next_values == [0, 1, 1, 1, 2, 3, 4]

text, pat = 'ababa', 'aba'
starts, comparisons = [], 0
for i in range(len(text) - len(pat) + 1):
    for j in range(len(pat)):
        comparisons += 1
        if text[i+j] != pat[j]:
            break
    else:
        starts.append(i)
assert starts == [0, 2] and comparisons == 7

print("non-code tree, traversal, sorting, counting, search and graph checks passed")
