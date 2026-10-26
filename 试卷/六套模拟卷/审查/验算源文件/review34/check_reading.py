import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
FILLS = {
    'S3-I01': [],
    'S3-I02': ['head->next', 'p->next', 'q->key < best->key'],
    'S3-I03': ['q->rear->next = p', 'q->rear = q->front', 'q->front == q->rear'],
    'S3-I04': ['g[u][v] && !seen[v]', 'dfs(v)', '!seen[u]'],
    'S4-I01': [],
    'S4-I02': ['pa', 'free(pa)', 'pb = pb->next'],
    'S4-I03': ['q->count == 4', '(q->rear + 1) % 4', '--q->count'],
    'S4-I04': ['t == NULL', 't->left == NULL && t->right == NULL', 'leafCount(t->left) + leafCount(t->right)'],
}

for paper in (3, 4):
    src = json.loads((ROOT / f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json').read_text(encoding='utf-8'))
    for q in src['questions'][:4]:
        code = re.search(r'```c\n(.*?)\n```', q['content'], re.S).group(1)
        for i, v in enumerate(FILLS[q['id']], 1):
            code = code.replace(f'__{i}__', v)
        assert '__' not in code
        source = HERE / f'{q["id"]}.c'
        exe = HERE / f'{q["id"]}.exe'
        source.write_text(code, encoding='utf-8')
        has_main = 'int main(' in code
        cmd = [GCC, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(source)]
        if has_main:
            cmd += ['-o', str(exe)]
        else:
            cmd += ['-c', '-o', str(HERE / f'{q["id"]}.o')]
        comp = subprocess.run(cmd, capture_output=True, text=True)
        if comp.returncode:
            print(q['id'], 'COMPILE ERROR', comp.stderr)
            raise SystemExit(1)
        if has_main:
            run = subprocess.run([str(exe)], capture_output=True, text=True)
            if run.returncode:
                print(q['id'], 'RUN ERROR', run.stderr)
                raise SystemExit(1)
            print(q['id'], repr(run.stdout.strip()))
        else:
            print(q['id'], 'COMPILE OK (no main)')
