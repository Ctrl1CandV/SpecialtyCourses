#!/usr/bin/env python3
"""Recompute selected exam data and compare algorithm prototypes with small oracles.

This verifies design seeds, not all final question wording, blanks or C code.
Bindings must be reviewed when task/data/answer changes; never auto-rebind here.
"""
import argparse
import hashlib
import heapq
import itertools
import json
from collections import deque
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'试卷/六套模拟卷/命题依据'


def signature(row):
    payload = {k: row.get(k, '') for k in ('task', 'data', 'answer_blueprint')}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def huffman(weights):
    heap = list(weights)
    heapq.heapify(heap)
    merged = []
    while len(heap) > 1:
        x = heapq.heappop(heap) + heapq.heappop(heap)
        merged.append(x)
        heapq.heappush(heap, x)
    return merged, sum(merged)


def hashing(keys, m):
    table = [None]*m
    successes = []
    for key in keys:
        p, count = key % m, 1
        while table[p] is not None:
            p, count = (p+1) % m, count+1
        table[p] = key
        successes.append(count)
    failures = []
    for start in range(m):
        p, count = start, 1
        while table[p] is not None:
            p, count = (p+1) % m, count+1
        failures.append(count)
    return {'table': table, 'success': successes, 'failure': failures,
            'ASL': [str(Fraction(sum(successes), len(keys))), str(Fraction(sum(failures), m))]}


def has_path_k(adj, u, w, v, k):
    if k < 0 or k >= len(adj):
        return False
    seen = {u}
    def search(x, depth, marked):
        if depth == k:
            return x == v and marked
        if x == v:
            return False
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                if search(y, depth+1, marked or y == w):
                    return True
                seen.remove(y)
        return False
    return search(u, 0, u == w)


def graph_edges(n, bits, directed=False):
    choices = [(u, v) for u in range(n) for v in range(n) if (u != v if directed else u < v)]
    return [edge for i, edge in enumerate(choices) if bits & (1 << i)]


def adjacency(n, edges, directed=False):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        if not directed:
            adj[v].append(u)
    return adj


def valid_order(order, n, edges):
    if sorted(order) != list(range(n)):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[u] < pos[v] for u, v in edges)


def prefix_possible(n, edges, prefix):
    if len(prefix) > n or len(set(prefix)) != len(prefix) or any(v < 0 or v >= n for v in prefix):
        return False
    adj = adjacency(n, edges, True)
    degree = [0]*n
    for _, v in edges:
        degree[v] += 1
    used = set()
    for x in prefix:
        if degree[x] != 0:
            return False
        used.add(x)
        for y in adj[x]:
            degree[y] -= 1
    q = deque(x for x in range(n) if x not in used and degree[x] == 0)
    done = len(used)
    while q:
        x = q.popleft()
        done += 1
        for y in adj[x]:
            degree[y] -= 1
            if degree[y] == 0:
                q.append(y)
    return done == n


def count_pairs(a, target):
    i, j, answer = 0, len(a)-1, 0
    while i < j:
        total = a[i]+a[j]
        if total < target:
            i += 1
        elif total > target:
            j -= 1
        elif a[i] == a[j]:
            r = j-i+1
            answer += r*(r-1)//2
            break
        else:
            left, right = a[i], a[j]
            il, jr = i, j
            while i <= j and a[i] == left:
                i += 1
            while j >= i and a[j] == right:
                j -= 1
            answer += (i-il)*(jr-j)
    return answer


def merge_k(lists):
    heap, out = [], []
    for i, seq in enumerate(lists):
        if seq:
            heapq.heappush(heap, (seq[0], i, 0))
    while heap:
        value, i, offset = heapq.heappop(heap)
        out.append((value, i, offset))
        if offset+1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][offset+1], i, offset+1))
    return out


def merge_into(a, b):
    m, n = len(a), len(b)
    out = list(a)+[None]*n
    i, j, k = m-1, n-1, m+n-1
    while j >= 0:
        if i >= 0 and out[i] > b[j]:
            out[k] = out[i]
            i -= 1
        else:
            out[k] = b[j]
            j -= 1
        k -= 1
    return out


def added_edge_class(n, edges, order, u, v):
    pos = {x: i for i, x in enumerate(order)}
    if u == v:
        return '有环'
    if pos[u] < pos[v]:
        return '原序可用'
    adj = adjacency(n, edges, True)
    seen, todo = {v}, [v]
    while todo:
        x = todo.pop()
        if x == u:
            return '有环'
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                todo.append(y)
    return '需重排'


def aoe(n, edges):
    # Here all fixtures number events in a topological order.
    ve = [0]*n
    for u in range(n):
        for a, b, w in edges:
            if a == u:
                ve[b] = max(ve[b], ve[a]+w)
    vl = [ve[-1]]*n
    for u in reversed(range(n)):
        for a, b, w in edges:
            if a == u:
                vl[a] = min(vl[a], vl[b]-w)
    return {'ve': ve, 'vl': vl, 'critical': [[u, v] for u, v, w in edges if ve[u] == vl[v]-w]}


def tree_diameter(tree):
    best = [0, None, None]
    def visit(node):
        if node is None:
            return -1, None
        name, left, right = node
        lh, le = visit(left)
        rh, re = visit(right)
        ll, rr = lh+1, rh+1
        le = le if left else name
        re = re if right else name
        if best[1] is None or ll+rr > best[0]:
            best[:] = [ll+rr, le, re]
        return (ll, le) if ll >= rr else (rr, re)
    visit(tree)
    return best


def traverse(tree):
    if not tree:
        return [], [], []
    x, l, r = tree
    lp, li, lo = traverse(l)
    rp, ri, ro = traverse(r)
    return [x]+lp+rp, li+[x]+ri, lo+ro+[x]


def post_from_pre_in(pre, inorder):
    pos = {v: i for i, v in enumerate(inorder)}
    out = []
    def emit(start, left, length):
        if length == 0:
            return
        root = pre[start]
        nleft = pos[root]-left
        emit(start+1, left, nleft)
        emit(start+1+nleft, pos[root]+1, length-nleft-1)
        out.append(root)
    emit(0, 0, len(pre))
    return out


def naive_prefix_table(pattern):
    """Compute each proper border directly, independently of a KMP update rule."""
    table = []
    for end in range(1, len(pattern)+1):
        prefix = pattern[:end]
        table.append(max(
            (length for length in range(1, end)
             if prefix[:length] == prefix[-length:]),
            default=0,
        ))
    return table


def run_checks():
    results = []
    def ensure_equal(actual, expected, context):
        if actual != expected:
            raise AssertionError(f'{context}: {actual!r} != {expected!r}')

    def record(qid, name, inputs, actual, expected):
        ensure_equal(actual, expected, f'{qid} {name}')
        results.append({'id': qid, 'name': name, 'inputs': inputs, 'result': actual, 'passed': True})

    first = huffman([3, 5, 7, 9, 20])
    second = huffman([6, 5, 7, 9, 20])
    record('S1-III02', '频率扰动：两个最优成本与旧码新成本', '3,5,7,9,20；A改6；旧码长4,4,3,2,1',
           [list(first[0]), first[1], 6*4+5*4+7*3+9*2+20, list(second[0]), second[1]],
           [[8,15,24,44],91,103,[11,16,27,47],101])
    record('S1-III03', '线性探测独立构表', {'keys':[14,25,36,5,16],'m':11}, hashing([14,25,36,5,16],11),
           {'table':[None,None,None,14,25,36,5,16,None,None,None], 'success':[1,2,3,2,3],
            'failure':[1,1,1,6,5,4,3,2,1,1,1], 'ASL':['11/5','26/11']})
    checks = 0
    for bits in range(64):
        adj = adjacency(4, graph_edges(4, bits))
        for k in range(-1,5):
            oracle = False
            if 1 <= k <= 3:
                for middle in itertools.permutations([1,2], k-1):
                    path = (0,)+middle+(3,)
                    if 1 in path and all(y in adj[x] for x,y in zip(path,path[1:])):
                        oracle = True
            ensure_equal(has_path_k(adj,0,1,3,k), oracle,
                         f'S2-IV03 bits={bits}, k={k}')
            checks += 1
    record('S2-IV03', '回溯原型与所有简单顶点排列交叉比较', '4顶点全部64无向图，u0/w1/v3，k=-1..4', checks, 384)
    cells = [(i,j) for i in range(6) for j in range(6) if abs(i-j)<=1]
    for k,(i,j) in enumerate(cells):
        ensure_equal(k, 2*i+j, f'S3-III01 A[{i},{j}]')
    record('S3-III01','三对角逐单元枚举','n=6，行主序0基',[len(cells),cells.index((4,3)),list(cells[15])],[16,11,[5,5]])
    seqs = [[], [1], [1,1], [0,2], [-1,1,2]]
    checks = 0
    for lists in itertools.product(seqs,repeat=3):
        expected = sorted((v,i,j) for i,a in enumerate(lists) for j,v in enumerate(a))
        ensure_equal(merge_k(lists), expected, f'S3-IV03 lists={lists!r}')
        checks += 1
    record('S3-IV03','堆归并原型与身份排序交叉核对','三链，空/重复/负键，共125组',checks,125)
    codes = {'000':'A','001':'B','01':'C','10':'D','11':'E'}
    def decode(bits):
        out, pending = '', ''
        for ch in bits:
            pending += ch
            if pending in codes:
                out += codes[pending]
                pending = ''
        return [out,pending]
    record('S4-III07','逐位译码与截断余串','001100001101；及删最后一位',
           [decode('001100001101'), decode('00110000110')],[['BDAEC',''],['BDAE','0']])
    stable = [('21a',21),('12',12),('21b',21),('11',11),('22',22),('10',10)]
    ones = sorted(stable,key=lambda x:x[1]%10)
    tens = sorted(ones,key=lambda x:x[1]//10)
    wrong = []
    for digit in range(10):
        wrong.extend(reversed([x for x in stable if x[1]%10==digit]))
    bad_final = sorted(wrong,key=lambda x:x[1]//10)
    record('S5-III07','稳定分配与个位桶LIFO的身份顺序',stable,
           [[x[0] for x in a] for a in (ones,tens,wrong,bad_final)],
           [['10','21a','21b','11','12','22'],['10','11','12','21a','21b','22'],
            ['10','11','21b','21a','22','12'],['10','11','12','21b','21a','22']])
    checks = 0
    for pair in itertools.product(range(100), repeat=2):
        buckets = [[] for _ in range(10)]
        for value in pair:
            buckets[value % 10].append(value)
        first_pass = [v for bucket in buckets for v in reversed(bucket)]
        result = sorted(first_pass, key=lambda v: v // 10)
        ensure_equal(result, sorted(pair), f'S5-III07 numeric-order pair={pair}')
        checks += 1
    record('S5-III07','个位桶LIFO、十位稳定时的数值排序交叉核对',
           '0..99全部双元素输入；一般性仍由位序不变量证明',checks,10000)
    checks = 0
    for n in range(7):
        for a in itertools.combinations_with_replacement(range(-2,3),n):
            for target in range(-5,6):
                oracle = sum(a[i]+a[j]==target for i in range(n) for j in range(i+1,n))
                ensure_equal(count_pairs(a,target), oracle,
                             f'S5-IV01 a={a!r}, target={target}')
                checks += 1
    record('S5-IV01','双指针原型与下标对穷举','长度0..6，值-2..2，K=-5..5',checks,5082)
    checks = 0
    prefixes = [()] + [p for k in range(1,4) for p in itertools.permutations(range(3),k)] + [(0,0),(-1,),(3,),(0,1,2,0)]
    for bits in range(64):
        edges = graph_edges(3,bits,True)
        orders = [p for p in itertools.permutations(range(3)) if valid_order(p,3,edges)]
        for prefix in prefixes:
            oracle = any(p[:len(prefix)] == prefix for p in orders)
            ensure_equal(prefix_possible(3,edges,prefix), oracle,
                         f'S5-IV02 edges={edges!r}, prefix={prefix!r}')
            checks += 1
    record('S5-IV02','前缀算法与全部拓扑排列交叉比较','3顶点全部64有向无自环图，含非法前缀',checks,1280)
    leaf = lambda x: (x,None,None)
    tree = ('R',('L',('A',leaf('C'),leaf('E')),('B',leaf('D'),leaf('F'))),None)
    record('S5-IV03','最长路径不经过整树根的端点实例','R(L(A(C,E),B(D,F)),空)',tree_diameter(tree),[4,'C','D'])
    record('S5-IV03','空树与单结点','空；X',[tree_diameter(None),tree_diameter(leaf('X'))],[[0,None,None],[0,'X','X']])
    p, text = 'abaaba', 'abaabaab'+'aaba'
    record('S6-III01','π表逐位朴素前后缀核对',p,
           naive_prefix_table(p),[0,0,1,1,2,3])
    record('S6-III01','按子串枚举交叉核对重叠匹配','P=abaaba，T1=abaabaab，T2=aaba',
           [i+1 for i in range(len(text)-len(p)+1) if text[i:i+len(p)]==p],[1,4,7])
    # Boundary retained after block: longest pattern prefix that is a suffix.
    q = max(i for i in range(len(p)) if 'abaabaab'.endswith(p[:i]))
    boundary = max(i for i in range(len(p)) if p.endswith(p[:i]))
    record('S6-III01','块末状态与成功后边界','已匹配长度接口',[q,boundary],[5,3])
    layers = []
    def binary_tree(lo,hi,depth):
        if lo>hi:
            return
        mid=(lo+hi)//2
        layers.append(depth)
        binary_tree(lo,mid-1,depth+1)
        binary_tree(mid+1,hi,depth+1)
    binary_tree(1,11,1)
    record('S6-III03','下标判定树及均匀ASL','闭区间1..11，mid向下',
           [[layers.count(d) for d in range(1,5)],str(Fraction(sum(layers),11)),[(7+11)//2,(7+8)//2]],[[1,2,4,4],'3',[9,7]])
    edges = [(0,1,2),(0,2,3),(1,3,4),(2,3,1),(2,4,4),(3,5,3),(4,5,2),(1,4,1)]
    after = [(u,v,4 if (u,v)==(2,3) else w) for u,v,w in edges]
    record('S6-III05','AOE两次正反拓扑计算',edges,[aoe(6,edges),aoe(6,after)],
           [{'ve':[0,2,3,6,7,9],'vl':[0,2,3,6,7,9],'critical':[[0,1],[0,2],[1,3],[2,4],[3,5],[4,5]]},
            {'ve':[0,2,3,7,7,10],'vl':[0,3,3,7,8,10],'critical':[[0,2],[2,3],[3,5]]}])
    arrs = [tuple(a) for n in range(4) for a in itertools.combinations_with_replacement((-1,0,1),n)]
    checks = 0
    for a,b in itertools.product(arrs,repeat=2):
        ensure_equal(merge_into(a,b), sorted(a+b),
                     f'S6-IV01 A={a!r}, B={b!r}')
        checks += 1
    record('S6-IV01','逆向归并原型与排序结果交叉比较','长度0..3，各值-1,0,1，含全重复与空输入',checks,400)
    pre,inorder=[0,1,3,4,2,5],[3,1,4,0,5,2]
    record('S6-IV02','不建树遍历转换样例',[pre,inorder],post_from_pre_in(pre,inorder),[3,4,1,5,2,0])
    record('S6-IV02','空、单结点和单右链边界','pre/in分别空、[0]、[0,1,2]',
           [post_from_pre_in([],[]),post_from_pre_in([0],[0]),post_from_pre_in([0,1,2],[0,1,2])],[[],[0],[2,1,0]])
    checks = 0
    orders = list(itertools.permutations(range(4)))
    for bits in range(64):
        base_edges = graph_edges(4,bits)
        for original_order in orders:
            edges = [(original_order[a],original_order[b])
                     for a,b in base_edges]
            for u,v in itertools.product(range(4),repeat=2):
                updated = edges+[(u,v)]
                if valid_order(original_order,4,updated):
                    oracle='原序可用'
                elif any(valid_order(order,4,updated) for order in orders):
                    oracle='需重排'
                else:
                    oracle='有环'
                ensure_equal(added_edge_class(4,edges,original_order,u,v),
                             oracle,
                             f'S6-IV03 bits={bits}, order={original_order!r}, '
                             f'edge=({u},{v})')
                checks += 1
    record('S6-IV03','增边三类判据与全部顶点排列交叉比较',
           '64个按拓扑位置生成的DAG×24种顶点重标号×16条可能新弧，含自环和已有弧',
           checks,24576)
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='write verified report after input bindings pass')
    args=parser.parse_args()
    rows={r['id']:r for r in json.loads((PLAN/'六套逐题蓝图.json').read_text(encoding='utf-8'))}
    bindings=json.loads((PLAN/'核验输入绑定.json').read_text(encoding='utf-8'))
    for qid, expected in bindings['design_hashes'].items():
        if signature(rows[qid])!=expected:
            raise SystemExit(f'{qid}: task/data/answer changed; review fixtures before updating the binding')
    records=run_checks()
    covered=sorted({r['id'] for r in records})
    if set(covered)!=set(bindings['design_hashes']):
        raise SystemExit('Binding IDs must equal the executed check IDs')
    for r in records:
        r['design_hash']=bindings['design_hashes'][r['id']]
    report={'version':bindings['version'],'kind':'设计数据与算法原型核验',
            'limitations':'硬编码fixture与题面对应关系仍须人工逐项核对；任务/数据/答案蓝图哈希仅阻止无审查变更。未验证全部144题、最终填空与代码空、配图、C代码内存语义或真实作答耗时；穷举小输入不代替一般正确性证明。',
            'count':len(records),'covered_ids':covered,'records':records}
    encoded=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    target=PLAN/'蓝图数据复核.json'
    if args.write:
        target.write_text(encoded,encoding='utf-8')
    elif not target.exists() or target.read_text(encoding='utf-8')!=encoded:
        raise SystemExit('核验计算通过，但报告未更新；运行 --write')
    print(f'PASS: {len(records)} selected checks covering {len(covered)} design slots; all bound inputs match')


if __name__=='__main__':
    main()
