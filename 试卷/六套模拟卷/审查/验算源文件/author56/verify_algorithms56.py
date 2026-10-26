"""Compile and exercise every paper 5/6 algorithm-design reference solution."""

import json
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GCC = Path("D:/Program Files/mingw64/bin/gcc.exe")
ANSWER_DIR = ROOT / "资料整理/六套模拟卷成稿/答案源稿"
rows = {}
for paper in (5, 6):
    data = json.loads((ANSWER_DIR / f"第{paper}套.json").read_text(encoding="utf-8"))
    rows.update({q["id"]: q for q in data["questions"]})

F = re.escape(chr(96) * 3)


def solution(qid):
    m = re.search(F + r"c\n(.*?)\n" + F, rows[qid]["content"], re.S)
    if m is None:
        raise ValueError(f"{qid}: no C block")
    return m.group(1)


HARNESSES = {
    "S5-IV01": r'''
#include <assert.h>
#include <stdio.h>
int main(void) {
    Node empty = {0, NULL};
    keepLastOfEachKey(&empty);
    assert(empty.next == NULL);
    srand(11);
    for (int rep = 0; rep < 400; ++rep) {
        Node head = {0, NULL}, *tail = &head;
        Node *last[32] = {0};
        int key = 0, count = 1 + rand() % 24;
        for (int i = 0; i < count; ++i) {
            if (i != 0 && rand() % 3 == 0) ++key;
            Node *p = malloc(sizeof *p);
            assert(p != NULL);
            p->key = key; p->next = NULL;
            tail->next = p; tail = p;
            last[key] = p;
        }
        keepLastOfEachKey(&head);
        int prev = -1, actual = 0, expected = 0;
        for (int k = 0; k < 32; ++k) if (last[k]) ++expected;
        Node *p = head.next;
        while (p != NULL) {
            assert(p->key > prev && p == last[p->key]);
            prev = p->key; ++actual;
            Node *next = p->next; free(p); p = next;
        }
        assert(actual == expected);
    }
    puts("S5-IV01 random and boundary checks pass");
    return 0;
}
''',
    "S5-IV02": r'''
#include <assert.h>
#include <stdio.h>
static int brute(const Graph *G, const int P[], int k, int used[],
                 int indeg[], int at) {
    if (at == G->V) return 1;
    for (int u = 0; u < G->V; ++u) {
        if (used[u] || indeg[u] != 0 || (at < k && P[at] != u)) continue;
        used[u] = 1;
        for (const Arc *e = G->head[u]; e; e = e->next) --indeg[e->to];
        if (brute(G, P, k, used, indeg, at + 1)) {
            for (const Arc *e = G->head[u]; e; e = e->next) ++indeg[e->to];
            used[u] = 0;
            return 1;
        }
        for (const Arc *e = G->head[u]; e; e = e->next) ++indeg[e->to];
        used[u] = 0;
    }
    return 0;
}
int main(void) {
    Graph zero = {0, NULL};
    assert(canBePrefix(&zero, NULL, 0));
    srand(12);
    for (int rep = 0; rep < 250; ++rep) {
        int V = 1 + rand() % 6;
        Arc arcs[36]; Arc *head[6] = {0};
        int E = 0;
        for (int u = 0; u < V; ++u)
            for (int v = u + 1; v < V; ++v)
                if (rand() % 3 == 0) {
                    arcs[E] = (Arc){v, head[u]};
                    head[u] = &arcs[E++];
                }
        Graph G = {V, head};
        int P[6]; for (int i = 0; i < V; ++i) P[i] = i;
        for (int i = V - 1; i > 0; --i) {
            int j = rand() % (i + 1), t = P[i]; P[i] = P[j]; P[j] = t;
        }
        for (int k = 0; k <= V; ++k) {
            int used[6] = {0}, indeg[6] = {0};
            for (int u = 0; u < V; ++u)
                for (Arc *e = head[u]; e; e = e->next) ++indeg[e->to];
            int want = brute(&G, P, k, used, indeg, 0);
            assert((int)canBePrefix(&G, P, k) == want);
        }
    }
    puts("S5-IV02 random DAG/topological-prefix checks pass");
    return 0;
}
''',
    "S5-IV03": r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static int bruteDiameter(int n, int adj[12][12]) {
    int best = 0;
    for (int start = 0; start < n; ++start) {
        int q[12], dist[12], front = 0, rear = 0;
        for (int i = 0; i < n; ++i) dist[i] = -1;
        dist[start] = 0; q[rear++] = start;
        while (front < rear) {
            int u = q[front++];
            for (int v = 0; v < n; ++v) if (adj[u][v] && dist[v] < 0) {
                dist[v] = dist[u] + 1; q[rear++] = v;
                if (dist[v] > best) best = dist[v];
            }
        }
    }
    return best;
}
int main(void) {
    assert(treeDiameter(NULL) == 0);
    srand(13);
    for (int rep = 0; rep < 400; ++rep) {
        int n = 1 + rand() % 12;
        Node nodes[12] = {0};
        int adj[12][12] = {{0}};
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (nodes[parent].left && nodes[parent].right);
            if (!nodes[parent].left && (!nodes[parent].right || rand() % 2))
                nodes[parent].left = &nodes[i];
            else
                nodes[parent].right = &nodes[i];
            adj[parent][i] = adj[i][parent] = 1;
        }
        assert(treeDiameter(&nodes[0]) == bruteDiameter(n, adj));
    }
    puts("S5-IV03 random-tree/all-pairs-distance checks pass");
    return 0;
}
''',
    "S6-IV01": r'''
#include <assert.h>
#include <stdio.h>
int main(void) {
    assert(symmetricDiff(NULL, NULL) == NULL);
    srand(14);
    for (int rep = 0; rep < 400; ++rep) {
        Node *A = NULL, *B = NULL, **ta = &A, **tb = &B;
        Node *expected[30] = {0};
        int common[30] = {0}, membershipA[30] = {0}, membershipB[30] = {0};
        for (int key = 0; key < 30; ++key) {
            membershipA[key] = rand() % 2;
            membershipB[key] = rand() % 2;
            if (membershipA[key]) {
                Node *p = malloc(sizeof *p); assert(p);
                p->key = key; p->next = NULL; *ta = p; ta = &p->next;
                expected[key] = p;
            }
            if (membershipB[key]) {
                Node *p = malloc(sizeof *p); assert(p);
                p->key = key; p->next = NULL; *tb = p; tb = &p->next;
                if (!membershipA[key]) expected[key] = p;
            }
            common[key] = membershipA[key] && membershipB[key];
        }
        Node *out = symmetricDiff(A, B);
        int prev = -1, count = 0, want = 0;
        for (int k = 0; k < 30; ++k) if ((membershipA[k] != 0) != (membershipB[k] != 0)) ++want;
        while (out) {
            assert(out->key > prev && out == expected[out->key] && !common[out->key]);
            prev = out->key; ++count;
            Node *next = out->next; free(out); out = next;
        }
        assert(count == want);
    }
    puts("S6-IV01 random-set/surviving-node-identity checks pass");
    return 0;
}
''',
    "S6-IV02": r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct TestNode { int key, left, right; } TestNode;
static TestNode nodes[16];
static int pre[16], in[16], want[16], post[16], pc, ic, wc;
static void emitPre(int x) {
    if (x < 0) return;
    pre[pc++] = nodes[x].key;
    emitPre(nodes[x].left); emitPre(nodes[x].right);
}
static void emitIn(int x) {
    if (x < 0) return;
    emitIn(nodes[x].left); in[ic++] = nodes[x].key; emitIn(nodes[x].right);
}
static void emitPost(int x) {
    if (x < 0) return;
    emitPost(nodes[x].left); emitPost(nodes[x].right);
    want[wc++] = nodes[x].key;
}
int main(void) {
    toPost(NULL, NULL, 0, NULL);
    srand(15);
    for (int rep = 0; rep < 400; ++rep) {
        int n = 1 + rand() % 15;
        for (int i = 0; i < n; ++i)
            nodes[i] = (TestNode){100 + 3*i, -1, -1};
        for (int i = 1; i < n; ++i) {
            int p; do { p = rand() % i; }
            while (nodes[p].left >= 0 && nodes[p].right >= 0);
            if (nodes[p].left < 0 && (nodes[p].right >= 0 || rand()%2))
                nodes[p].left = i;
            else
                nodes[p].right = i;
        }
        pc = ic = wc = 0;
        emitPre(0); emitIn(0); emitPost(0);
        assert(pc == n && ic == n && wc == n);
        toPost(pre, in, n, post);
        for (int i = 0; i < n; ++i) assert(post[i] == want[i]);
    }
    puts("S6-IV02 random-tree/pre-in-post checks pass");
    return 0;
}
''',
    "S6-IV03": r'''
#include <assert.h>
#include <stdio.h>
static int expected(int n, int matrix[7][7], int sigma[], int u, int v) {
    int indeg[7] = {0}, used[7] = {0}, count = 0;
    for (int a = 0; a < n; ++a)
        for (int b = 0; b < n; ++b)
            if (matrix[a][b] || (a == u && b == v)) ++indeg[b];
    for (;;) {
        int picked = -1;
        for (int x = 0; x < n; ++x)
            if (!used[x] && indeg[x] == 0) { picked = x; break; }
        if (picked < 0) break;
        used[picked] = 1; ++count;
        for (int b = 0; b < n; ++b)
            if (matrix[picked][b] || (picked == u && b == v)) --indeg[b];
    }
    if (count != n) return CYCLE;
    int pu = -1, pv = -1;
    for (int i = 0; i < n; ++i) {
        if (sigma[i] == u) pu = i;
        if (sigma[i] == v) pv = i;
    }
    return pu < pv ? ORDER_OK : REORDER;
}
int main(void) {
    srand(16);
    int observed[3] = {0};
    for (int rep = 0; rep < 250; ++rep) {
        int n = 2 + rand() % 6;
        int sigma[7], pos[7], matrix[7][7] = {{0}};
        Arc arcs[49], *head[7] = {0};
        int E = 0;
        for (int i = 0; i < n; ++i) sigma[i] = i;
        for (int i = n - 1; i > 0; --i) {
            int j = rand() % (i + 1), t = sigma[i];
            sigma[i] = sigma[j]; sigma[j] = t;
        }
        for (int i = 0; i < n; ++i) pos[sigma[i]] = i;
        for (int u = 0; u < n; ++u)
            for (int v = 0; v < n; ++v)
                if (pos[u] < pos[v] && rand() % 3 == 0) {
                    matrix[u][v] = 1;
                    arcs[E] = (Arc){v, head[u]}; head[u] = &arcs[E++];
                }
        Graph G = {n, head};
        for (int u = 0; u < n; ++u)
            for (int v = 0; v < n; ++v)
                if (!matrix[u][v]) {
                    State got = classifyArc(&G, sigma, u, v);
                    int want = expected(n, matrix, sigma, u, v);
                    assert((int)got == want);
                    ++observed[got];
                }
        for (int u = 0; u < n; ++u) {
            int seen[7] = {0};
            for (Arc *e = head[u]; e; e = e->next) seen[e->to] = 1;
            for (int v = 0; v < n; ++v) assert(seen[v] == matrix[u][v]);
        }
    }
    assert(observed[ORDER_OK] && observed[REORDER] && observed[CYCLE]);
    puts("S6-IV03 random-DAG/rebuild-and-check-state checks pass");
    return 0;
}
''',
}


for qid, harness in HARNESSES.items():
    src = HERE / f"{qid}.verify.c"
    exe = HERE / f"{qid}.verify.exe"
    src.write_text(solution(qid) + "\n" + harness, encoding="utf-8")
    built = subprocess.run(
        [str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)],
        capture_output=True, text=True,
    )
    if built.returncode != 0:
        raise RuntimeError(f"{qid} compile failed:\n{built.stderr}")
    ran = subprocess.run([str(exe)], capture_output=True, text=True)
    if ran.returncode != 0:
        raise RuntimeError(f"{qid} test failed with {ran.returncode}:\n{ran.stderr}")
    print(ran.stdout.strip())
