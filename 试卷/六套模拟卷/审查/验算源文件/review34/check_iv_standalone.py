import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
for paper in (3, 4):
    doc = json.loads((ROOT / f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json').read_text(encoding='utf-8'))
    for q in doc['questions']:
        if '-IV' not in q['id']:
            continue
        code = re.search(r'```c\n(.*?)\n```', q['content'], re.S).group(1)
        src = HERE / f'{q["id"]}-standalone.c'
        obj = src.with_suffix('.o')
        src.write_text(code, encoding='utf-8')
        result = subprocess.run([GCC, '-std=c11', '-Wall', '-Wextra', '-Werror', '-c', str(src), '-o', str(obj)], capture_output=True, text=True)
        if result.returncode:
            print(q['id'], result.stderr)
            raise SystemExit(1)
        print(q['id'], 'strict standalone compile OK')
