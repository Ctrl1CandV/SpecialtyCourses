"""Compile all eight filled program-reading snippets from the current student papers."""

import json
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GCC = Path("D:/Program Files/mingw64/bin/gcc.exe")
SOURCE = ROOT / "资料整理/六套模拟卷成稿/试题源稿"
rows = {}
for paper in (5, 6):
    data = json.loads((SOURCE / f"第{paper}套.json").read_text(encoding="utf-8"))
    rows.update({q["id"]: q for q in data["questions"] if q["section"] == "I"})

filled = {
    "S5-I01": {},
    "S5-I02": {1: "pre->next", 2: "p", 3: "p->next"},
    "S5-I03": {1: "CAP", 2: "s->top0 + 1 == s->top1", 3: "s->top1 == CAP"},
    "S5-I04": {1: "key % m", 2: "(pos + 1) % m"},
    "S6-I01": {},
    "S6-I02": {1: "a != NULL || b != NULL", 2: "a->key <= b->key"},
    "S6-I03": {1: "size(q)", 2: "p->left == NULL && p->right == NULL"},
    "S6-I04": {1: "!empty(q)", 2: "--indeg[e->to] == 0"},
}

extra = {
    "S5-I02": r'''
#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    Node head = {0, NULL}, *tail = &head;
    int x[] = {2, 4, 5, 6, 7, 8};
    for (int i = 0; i < 6; ++i) {
        Node *p = malloc(sizeof *p);
        assert(p);
        *p = (Node){x[i], NULL}; tail->next = p; tail = p;
    }
    removeEven(&head);
    assert(head.next && head.next->data == 5);
    assert(head.next->next && head.next->next->data == 7);
    assert(head.next->next->next == NULL);
    free(head.next->next); free(head.next);
    Node empty = {0, NULL}; removeEven(&empty);
    assert(empty.next == NULL);
    return 0;
}
''',
    "S5-I03": r'''
#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    Shared s; int out;
    init(&s);
    assert(pop1(&s, &out) == 0);
    for (int i = 0; i < CAP; ++i) assert(push0(&s, i) == 1);
    assert(full(&s) && push1(&s, 100) == 0);
    init(&s);
    assert(push1(&s, 71) == 1 && pop1(&s, &out) == 1 && out == 71);
    assert(pop1(&s, &out) == 0);
    return 0;
}
''',
    "S5-I04": r'''
#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    int a[3] = {0, 1, 2};
    assert(insertLinear(a, 3, 3) == 0);
    int b[3] = {-1, -1, -1};
    assert(insertLinear(b, 3, 4) == 1);
    assert(insertLinear(b, 3, 7) == 1);
    assert(insertLinear(b, 3, 10) == 1);
    assert(b[0] == 10 && b[1] == 4 && b[2] == 7);
    return 0;
}
''',
    "S6-I02": r'''
#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    assert(mergeReverse(NULL, NULL) == NULL);
    Node a = {3, NULL}, b = {3, NULL};
    Node *out = mergeReverse(&a, &b);
    assert(out == &b && out->next == &a);
    return 0;
}
''',
    "S6-I03": r'''
#include <assert.h>
#include <stdio.h>
struct Queue { Node *a[32]; int front, rear; };
int empty(const Queue *q) { return q->front == q->rear; }
int size(const Queue *q) { return q->rear - q->front; }
Node *dequeue(Queue *q) { return q->a[q->front++]; }
void enqueue(Queue *q, Node *p) { q->a[q->rear++] = p; }
int main(void) {
    Queue q = {0};
    assert(sample(&q) == 8);
    Queue other = {0};
    assert(weightedLeaves(NULL, &other) == 0);
    Node x = {NULL, NULL};
    assert(weightedLeaves(&x, &other) == 1);
    return 0;
}
''',
    "S6-I04": r'''
#include <assert.h>
#include <stdio.h>
struct Queue { int a[32], front, rear; };
int empty(const Queue *q) { return q->front == q->rear; }
void enqueue(Queue *q, int x) { q->a[q->rear++] = x; }
int dequeue(Queue *q) { return q->a[q->front++]; }
static int out[32], count;
void output(int x) { out[count++] = x; }
int main(void) {
    Queue q = {0};
    assert(sampleDag(&q) == 1);
    assert(count == 4 && out[0] == 0 && out[1] == 1
           && out[2] == 2 && out[3] == 3);
    Queue cyclic = {0};
    count = 0;
    assert(sampleCycle(&cyclic) == 0 && count == 0);
    return 0;
}
''',
}

expected_output = {
    "S5-I01": "2 -> 2\n4 -> 8\n8 -> 24\n",
    "S5-I02": "3 5 7 \n",
    "S5-I03": "72\n",
    "S5-I04": "-1 -1 -1 3 -1 -1 -1 7 18 29 -1 \n",
    "S6-I01": "n=65536 x=65536 count=4\n",
    "S6-I02": "4 3 3 3 2 1 \n",
    "S6-I03": "",
    "S6-I04": "",
}

for qid, replacement in filled.items():
    m = re.search(re.escape(chr(96)*3) + r"c\n(.*?)\n" + re.escape(chr(96)*3),
                  rows[qid]["content"], re.S)
    if m is None:
        raise ValueError(f"{qid}: missing C snippet")
    code = m.group(1)
    for number, value in replacement.items():
        token = f"__{number}__"
        if code.count(token) != 1:
            raise ValueError(f"{qid}: wrong code blank {token}")
        code = code.replace(token, value)
    if re.search(r"__\d+__", code):
        raise ValueError(f"{qid}: unfilled code")
    if qid in extra and "int main(void)" in code:
        code = "#define main original_main\n" + code + "\n#undef main\n" + extra[qid]
    else:
        code += "\n" + extra.get(qid, "")
    src = HERE / f"{qid}.reading.c"
    exe = HERE / f"{qid}.reading.exe"
    src.write_text(code, encoding="utf-8")
    built = subprocess.run(
        [str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", str(src), "-o", str(exe)],
        capture_output=True, text=True,
    )
    if built.returncode:
        raise RuntimeError(f"{qid} compile failed:\n{built.stderr}")
    ran = subprocess.run([str(exe)], capture_output=True, text=True)
    if ran.returncode or ran.stdout != expected_output[qid]:
        raise RuntimeError(f"{qid} run mismatch:\n{ran.stdout}\n{ran.stderr}")
    print(f"{qid}: compile and run pass")
