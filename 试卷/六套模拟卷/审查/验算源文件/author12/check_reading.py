import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
FILLS = {
    'S1-I01': [],
    'S1-I02': ['prev->next', 'p', 'prev->next'],
    'S1-I03': ['q->rear->next', 'q->rear = NULL', 'q->rear->next = x->next'],
    'S1-I04': ['0', '1', 'leafCount(t->left) + leafCount(t->right)'],
    'S2-I01': [],
    'S2-I02': ['q', 'y', 'q'],
    'S2-I03': ['s->topL + 1 == s->topR', '--s->topR', 's->topR++'],
    'S2-I04': ['0', 'a - b > 1 || b - a > 1', '1 + (a > b ? a : b)'],
}
for paper in (1, 2):
    src = ROOT / f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json'
    data = json.loads(src.read_text(encoding='utf-8'))
    for q in data['questions'][:4]:
        code = re.search(r'```c\n(.*?)\n```', q['content'], re.S).group(1)
        for i, value in enumerate(FILLS[q['id']], 1):
            code = code.replace(f'__{i}__', value)
        assert '__' not in code, q['id']
        cpath = HERE / f'{q["id"]}.c'
        exe = HERE / f'{q["id"]}.exe'
        cpath.write_text(code, encoding='utf-8')
        comp = subprocess.run([GCC, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(cpath), '-o', str(exe)], capture_output=True, text=True)
        if comp.returncode:
            print(q['id'], 'COMPILE FAIL', comp.stderr)
            raise SystemExit(1)
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        if run.returncode:
            print(q['id'], 'RUN FAIL', run.stderr)
            raise SystemExit(1)
        print(q['id'], 'OK', repr(run.stdout.strip()))
