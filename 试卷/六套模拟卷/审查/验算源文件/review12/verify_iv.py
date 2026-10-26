"""Independent randomized checks of the six paper 1/2 algorithm answers."""

import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).parent
GCC = pathlib.Path("D:/Program Files/mingw64/bin/gcc.exe")


def answer_code(paper, number):
    path = ROOT / f"资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    item = next(q for q in doc["questions"] if q["id"] == f"S{paper}-IV0{number}")
    blocks = re.findall(r"```c\n(.*?)\n```", item["content"], re.S)
    assert len(blocks) == 1
    return blocks[0]


TESTS = {
    (1, 1): r'''
int main(void) {
    for (int trial = 0; trial < 300; ++trial) {
        Node ah = {0, 0}, bh = {0, 0}, *at = &ah, *bt = &bh;
        int expected[50], en = 0, na = rand() % 25, nb = rand() % 25;
        int av[25], bv[25];
        for (int i = 0; i < na; ++i) av[i] = i * 3 - 20;
        for (int i = 0; i < nb; ++i) bv[i] = i * 2 - 20;
        for (int i = 0; i < na; ++i) {
            Node *x = malloc(sizeof(*x)); x->data = av[i]; x->next = 0;
            at->next = x; at = x;
            int has = 0;
            for (int j = 0; j < nb; ++j) if (av[i] == bv[j]) has = 1;
            if (!has) expected[en++] = av[i];
        }
        for (int i = 0; i < nb; ++i) {
            Node *x = malloc(sizeof(*x)); x->data = bv[i]; x->next = 0;
            bt->next = x; bt = x;
        }
        listDifference(&ah, &bh);
        Node *p = ah.next;
        for (int i = 0; i < en; ++i) { assert(p && p->data == expected[i]); p = p->next; }
        assert(!p);
        p = bh.next;
        for (int i = 0; i < nb; ++i) { assert(p && p->data == bv[i]); p = p->next; }
        assert(!p);
        while (ah.next) { p = ah.next; ah.next = p->next; free(p); }
        while (bh.next) { p = bh.next; bh.next = p->next; free(p); }
    }
    puts("S1-IV01 300 cases OK");
}
''',
    (1, 2): r'''
static int oracleBest(const TNode *p) {
    if (!p->left && !p->right) return p->data;
    if (!p->left) return p->data + oracleBest(p->right);
    if (!p->right) return p->data + oracleBest(p->left);
    int a = oracleBest(p->left), b = oracleBest(p->right);
    return p->data + (a > b ? a : b);
}
static int validPath(const TNode *p, const int path[], int len) {
    if (!p || len <= 0 || p->data != path[0]) return 0;
    if (len == 1) return !p->left && !p->right;
    return validPath(p->left, path + 1, len - 1) ||
           validPath(p->right, path + 1, len - 1);
}
int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        TNode node[30] = {0}; int n = 1 + rand() % 30;
        for (int i = 0; i < n; ++i) node[i].data = rand() % 31 - 15;
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (node[parent].left && node[parent].right);
            if (!node[parent].left && !node[parent].right && rand() % 2)
                node[parent].right = &node[i];
            else if (!node[parent].left) node[parent].left = &node[i];
            else node[parent].right = &node[i];
        }
        int path[30], len = -1, got = maxRootLeafSum(node, path, &len);
        assert(got == oracleBest(node));
        assert(len >= 1 && len <= n && validPath(node, path, len));
        int sum = 0; for (int i = 0; i < len; ++i) sum += path[i];
        assert(sum == got);
    }
    puts("S1-IV02 400 cases OK");
}
''',
    (1, 3): r'''
static int oracleReach(int n, int adj[12][12], int s, int t, int w) {
    int seen[12] = {0}, q[12], front = 0, rear = 0;
    seen[s] = 1; q[rear++] = s;
    while (front < rear) {
        int u = q[front++]; if (u == t) return 1;
        for (int v = 0; v < n; ++v)
            if (v != w && adj[u][v] && !seen[v]) { seen[v] = 1; q[rear++] = v; }
    }
    return 0;
}
int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        int n = 3 + rand() % 9, adj[12][12] = {0};
        Arc arc[150]; Arc *head[12] = {0}; int ec = 0, undirected = 0;
        for (int u = 0; u < n; ++u) for (int v = u + 1; v < n; ++v)
            if (rand() % 3 == 0) {
                adj[u][v] = adj[v][u] = 1; ++undirected;
                arc[ec] = (Arc){v, head[u]}; head[u] = &arc[ec++];
                arc[ec] = (Arc){u, head[v]}; head[v] = &arc[ec++];
            }
        Graph g = {n, undirected, head};
        int s = rand() % n, t, w, path[12], len = -1;
        do { t = rand() % n; } while (t == s);
        do { w = rand() % n; } while (w == s || w == t);
        int got = pathAvoidingVertex(&g, s, t, w, path, &len);
        assert(got == oracleReach(n, adj, s, t, w));
        if (!got) assert(len == 0);
        else {
            int seen[12] = {0}; assert(len >= 2 && len <= n);
            assert(path[0] == s && path[len-1] == t);
            for (int i = 0; i < len; ++i) {
                assert(path[i] != w && !seen[path[i]]); seen[path[i]] = 1;
                if (i) assert(adj[path[i-1]][path[i]]);
            }
        }
    }
    puts("S1-IV03 400 cases OK");
}
''',
    (2, 1): r'''
int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        Node h = {0, 0}, a[40]; int neg[40], nonneg[40], nn = 0, np = 0;
        int n = rand() % 41;
        for (int i = 0; i < n; ++i) {
            a[i].data = rand() % 21 - 10;
            a[i].next = i + 1 < n ? &a[i+1] : 0;
            if (a[i].data < 0) neg[nn++] = a[i].data;
            else nonneg[np++] = a[i].data;
        }
        h.next = n ? a : 0;
        stableNegFirst(&h);
        Node *p = h.next;
        for (int i = 0; i < nn; ++i) { assert(p && p->data == neg[i]); p = p->next; }
        for (int i = 0; i < np; ++i) { assert(p && p->data == nonneg[i]); p = p->next; }
        assert(!p);
    }
    puts("S2-IV01 400 cases OK");
}
''',
    (2, 2): r'''
static int oracleLeaves(TNode *p) {
    if (!p) return 0;
    if (!p->left && !p->right) return 1;
    return oracleLeaves(p->left) + oracleLeaves(p->right);
}
int main(void) {
    fillLeafCounts(0);
    for (int trial = 0; trial < 400; ++trial) {
        TNode node[30] = {0}; int n = 1 + rand() % 30;
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (node[parent].left && node[parent].right);
            if (!node[parent].left && !node[parent].right && rand() % 2)
                node[parent].right = &node[i];
            else if (!node[parent].left) node[parent].left = &node[i];
            else node[parent].right = &node[i];
        }
        fillLeafCounts(node);
        for (int i = 0; i < n; ++i) assert(node[i].count == oracleLeaves(&node[i]));
    }
    puts("S2-IV02 400 cases OK");
}
''',
    (2, 3): r'''
static int oracleDist(int n, int adj[12][12], int s, int t) {
    int dist[12], q[12], front = 0, rear = 0;
    for (int i = 0; i < n; ++i) dist[i] = -1;
    dist[s] = 0; q[rear++] = s;
    while (front < rear) {
        int u = q[front++]; if (u == t) return dist[u];
        for (int v = 0; v < n; ++v) if (adj[u][v] && dist[v] < 0) {
            dist[v] = dist[u] + 1; q[rear++] = v;
        }
    }
    return -1;
}
int main(void) {
    for (int trial = 0; trial < 500; ++trial) {
        int n = 1 + rand() % 10, adj[12][12] = {0};
        Arc arc[150]; Arc *head[12] = {0}; int ec = 0, undirected = 0;
        for (int u = 0; u < n; ++u) for (int v = u + 1; v < n; ++v)
            if (rand() % 3 == 0) {
                adj[u][v] = adj[v][u] = 1; ++undirected;
                arc[ec] = (Arc){v, head[u]}; head[u] = &arc[ec++];
                arc[ec] = (Arc){u, head[v]}; head[v] = &arc[ec++];
            }
        Graph g = {n, undirected, head};
        int s = rand() % n, t = rand() % n, k = rand() % 15 - 2;
        int path[12], len = -1, d = oracleDist(n, adj, s, t);
        int expect = k >= 0 && d >= 0 && d <= k;
        int got = pathAtMostK(&g, s, t, k, path, &len);
        assert(got == expect);
        if (!got) assert(len == 0);
        else {
            int seen[12] = {0}; assert(len >= 1 && len <= n && len - 1 <= k);
            assert(path[0] == s && path[len-1] == t);
            for (int i = 0; i < len; ++i) {
                assert(!seen[path[i]]); seen[path[i]] = 1;
                if (i) assert(adj[path[i-1]][path[i]]);
            }
        }
    }
    puts("S2-IV03 500 cases OK");
}
''',
}


def main():
    for (paper, number), test in TESTS.items():
        name = f"S{paper}-IV0{number}"
        source = "#include <assert.h>\n#include <stddef.h>\n#include <stdlib.h>\n#include <stdio.h>\n" + answer_code(paper, number) + "\n" + test
        src = OUT / f"{name}.c"
        exe = OUT / f"{name}.exe"
        src.write_text(source, encoding="utf-8")
        build = subprocess.run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)], capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(name + " compile failed:\n" + build.stderr)
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(name + " run failed:\n" + run.stderr)
        bare = OUT / f"standalone_{name}.c"
        bare.write_text(answer_code(paper, number), encoding="utf-8")
        bare_build = subprocess.run(
            [str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", "-c", str(bare), "-o", str(bare.with_suffix(".o"))],
            capture_output=True, text=True,
        )
        if bare_build.returncode:
            raise RuntimeError(name + " standalone compile failed:\n" + bare_build.stderr)
        print(run.stdout.strip())


if __name__ == "__main__":
    main()
