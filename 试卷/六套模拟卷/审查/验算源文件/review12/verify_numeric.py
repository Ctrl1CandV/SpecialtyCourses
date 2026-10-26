"""Independent small oracles for paper 1/2 numerical and process questions."""

from collections import deque
from heapq import heappop, heappush
from itertools import product


def pop_sequences(n):
    out = []
    def visit(next_in, stack, seq):
        if len(seq) == n:
            out.append(tuple(seq))
            return
        if next_in <= n:
            visit(next_in + 1, stack + (next_in,), seq)
        if stack:
            visit(next_in, stack[:-1], seq + (stack[-1],))
    visit(1, (), ())
    return out


def binary_depths(values):
    depth = {}
    failed = {}
    def scan(lo, hi, comparisons):
        if lo > hi:
            failed[lo] = comparisons
            return
        mid = (lo + hi) // 2
        depth[values[mid]] = comparisons + 1
        scan(lo, mid - 1, comparisons + 1)
        scan(mid + 1, hi, comparisons + 1)
    scan(0, len(values) - 1, 0)
    return depth, [failed[i] for i in range(len(values) + 1)]


def linear_hash(keys, m):
    table = [None] * m
    success = []
    for key in keys:
        j = key % m
        probes = 1
        while table[j] is not None:
            j = (j + 1) % m
            probes += 1
        table[j] = key
        success.append(probes)
    failure = []
    for start in range(m):
        j, probes = start, 1
        while table[j] is not None:
            j = (j + 1) % m
            probes += 1
        failure.append(probes)
    return table, success, failure


def huffman(weights):
    heap = [(w, s, s) for s, w in weights.items()]
    from heapq import heapify
    heapify(heap)
    merges = []
    while len(heap) > 1:
        a = heappop(heap)
        b = heappop(heap)
        merges.append((a[0], b[0], a[0] + b[0]))
        heappush(heap, (a[0] + b[0], min(a[1], b[1]), (a[2], b[2])))
    codes = {}
    def walk(node, bits):
        if isinstance(node, str):
            codes[node] = bits
        else:
            walk(node[0], bits + '0')
            walk(node[1], bits + '1')
    walk(heap[0][2], '')
    return merges, codes, sum(weights[s] * len(code) for s, code in codes.items())


def quick_hole(a):
    a = a[:]
    pivot, i, j = a[0], 0, len(a)-1
    while i < j:
        while i < j and a[j] >= pivot:
            j -= 1
        if i < j:
            a[i] = a[j]
            i += 1
        while i < j and a[i] <= pivot:
            i += 1
        if i < j:
            a[j] = a[i]
            j -= 1
    a[i] = pivot
    return a, i


def insertion_states(a):
    a = a[:]
    states = {}
    for i in range(1, len(a)):
        key, j = a[i], i - 1
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]
            j -= 1
        a[j+1] = key
        states[i] = a[:]
    return states


def small_heap(a):
    a = a[:]
    states = {}
    for start in reversed(range(len(a)//2)):
        root = start
        while 2*root+1 < len(a):
            child = 2*root+1
            if child+1 < len(a) and a[child+1] < a[child]:
                child += 1
            if a[root] <= a[child]:
                break
            a[root], a[child] = a[child], a[root]
            root = child
        states[start] = a[:]
    return states


def main():
    seq5 = pop_sequences(5)
    assert len(seq5) == 42
    assert sum(s[0] == 3 for s in seq5) == 9
    assert len(pop_sequences(4)) == 14
    print('S1-II07=9, S2-II02=14')

    assert sum(binary_depths([4,9,13,18,25,29,35,41,50,58])[0].values()) == 29
    depths2, fail2 = binary_depths([3,8,12,17,21,26,31,44])
    assert sum(depths2.values()) == 21 and fail2 == [3]*7 + [4]*2
    assert binary_depths(list(range(16)))[0][15] == 5
    print('S1-III04, S2-III02, S2-II08 binary search OK')

    t, s, f = linear_hash([14,25,36,5,16], 11)
    assert t == [None,None,None,14,25,36,5,16,None,None,None]
    assert s == [1,2,3,2,3] and f == [1,1,1,6,5,4,3,2,1,1,1]
    t, s, f = linear_hash([12,23,34,4,15,26,7], 11)
    assert t == [None,12,23,34,4,15,26,7,None,None,None]
    assert s == [1,2,3,1,2,3,1] and f == [1,8,7,6,5,4,3,2,1,1,1]
    print('S1-III03 and S2-III03 hash probes OK')

    merges, codes, wpl = huffman(dict(zip('ABCDE', [3,5,7,9,20])))
    assert merges == [(3,5,8),(7,8,15),(9,15,24),(20,24,44)]
    assert codes == {'E':'0','D':'10','C':'110','A':'1110','B':'1111'} and wpl == 91
    merges, codes, wpl = huffman(dict(zip('ABCDEF', [2,3,4,7,8,12])))
    assert merges == [(2,3,5),(4,5,9),(7,8,15),(9,12,21),(15,21,36)]
    assert codes == {'D':'00','E':'01','C':'100','A':'1010','B':'1011','F':'11'} and wpl == 86
    print('S1-III02 and S2-III06 Huffman OK')

    assert quick_hole([42,17,63,28,9,54,31,22]) == ([22,17,31,28,9,42,54,63],5)
    assert small_heap([42,17,63,28,9,54,31,22])[0] == [9,17,31,22,42,54,63,28]
    assert insertion_states([53,17,72,24,36,91,45,68])[4] == [17,24,36,53,72,91,45,68]
    assert insertion_states([53,17,72,24,36,91,45,68])[6] == [17,24,36,45,53,72,91,68]
    assert quick_hole([53,17,72,24,36,91,45,68]) == ([45,17,36,24,53,91,72,68],4)
    print('S1-III07 and S2-III07 sort processes OK')

    # Dijkstra and AOE small independent calculations.
    adj = {0:[(1,0),(2,4)],1:[(2,2),(3,7)],2:[(3,1),(4,6)],3:[(4,3)],4:[],5:[]}
    d = [float('inf')]*6; d[0] = 0; pq = [(0,0)]
    while pq:
        du,u = heappop(pq)
        if du != d[u]: continue
        for v,w in adj[u]:
            if du+w < d[v]:
                d[v] = du+w; heappush(pq,(d[v],v))
    assert d == [0,0,2,3,6,float('inf')]
    dur = {(0,1):3,(0,2):2,(1,3):2,(1,4):3,(2,3):4,(1,5):3,(3,5):2,(4,5):1}
    ve = [0]*6
    for u in range(6):
        for (a,b),w in dur.items():
            if a == u: ve[b] = max(ve[b],ve[a]+w)
    vl = [ve[5]]*6
    for u in reversed(range(6)):
        for (a,b),w in dur.items():
            if a == u: vl[a] = min(vl[a],vl[b]-w)
    assert ve == [0,3,2,6,6,8] and vl == [0,4,2,6,7,8]
    print('S2-III04 Dijkstra and S2-III05 AOE OK')


if __name__ == '__main__':
    main()
