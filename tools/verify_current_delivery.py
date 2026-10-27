"""Read-only integrity check for C3, 2027 papers and retained historical exports.

Uses only Python's standard library. Does not rebuild or modify deliverables.
An edited source/PPT/PDF is reported for review, never overwritten or re-signed.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hash(path, expected):
    if not path.is_file():
        raise ValueError(f'缺少文件：{path.relative_to(ROOT)}')
    if sha256(path) != expected:
        raise ValueError(f'文件已改动或版本不一致：{path.relative_to(ROOT)}')


def verify():
    courses = ROOT / '课程/课件/C3'
    lessons = read_json(courses / '维护/成品核对.json')['lessons']
    expected_ids = ['C3-A-01', 'C3-A-02'] + [f'C3-B-{i:02}' for i in range(1, 8)]
    if sorted(row['id'] for row in lessons) != expected_ids:
        raise ValueError('C3课程清单不是当前九节课')
    for row in lessons:
        ident = row['id']
        directory = courses / ident
        for name, key in [('deck.yaml', 'source_sha256'),
                          (f'{ident}-讲稿.md', 'lecture_sha256'),
                          (f'{ident}.pptx', 'pptx_sha256')]:
            check_hash(directory / name, row[key])
        check_hash(ROOT / '课程/素材/底图.jpg', row['background_sha256'])
        with ZipFile(directory / f'{ident}.pptx') as package:
            count = sum(bool(re.fullmatch(r'ppt/slides/slide\d+\.xml', n))
                        for n in package.namelist())
            if count != row['pages']:
                raise ValueError(f'{ident}页数与清单不符')
    print(f'C3：9节、{sum(r["pages"] for r in lessons)}页，三件套与底图指纹一致。')

    base = ROOT / '试卷/2027押题卷'
    papers = read_json(base / '审查/成卷核对.json')['papers']
    if sorted(row['paper'] for row in papers) != [1, 2, 3]:
        raise ValueError('押题卷清单不是当前三套卷')
    total = 0
    for row in papers:
        number = row['paper']
        source = base / '源稿' / f'第{number}套.json'
        check_hash(source, row['source_sha256'])
        data = read_json(source)
        qs = data['questions']
        if len(qs) != (24 if number == 1 else 25):
            raise ValueError(f'卷{number}题数不符')
        if [sum(q['points'] for q in qs if q['section'] == s)
                for s in ('I', 'II', 'III', 'IV')] != [20, 30, 70, 30]:
            raise ValueError(f'卷{number}分值不符')
        if len({q['id'] for q in qs}) != len(qs):
            raise ValueError(f'卷{number}存在重复题号')
        for kind in ('试卷', '答案', '讲解'):
            if not (base / '源稿' / kind / f'第{number}套{kind}.md').is_file():
                raise ValueError(f'卷{number}缺少{kind}可读源稿')
        if len(row['outputs']) != 2:
            raise ValueError(f'卷{number}PDF交付数量不符')
        for output in row['outputs']:
            path = base / output['file'].replace('\\', '/')
            check_hash(path, output['sha256'])
            if not path.read_bytes().startswith(b'%PDF-'):
                raise ValueError(f'PDF格式不符：{path.relative_to(ROOT)}')
        for q in qs:
            if q.get('figure') and not (base / '源稿/配图' / f'{q["id"]}.svg').is_file():
                raise ValueError(f'缺少配图：{q["id"]}')
        total += len(qs)
    print(f'押题卷：3套、{total}题，题源与6份PDF指纹一致，各卷150分。')
    archive = ROOT / '资料/历史参考/2026-10-04排版导出'
    records = read_json(archive / '存档核对.json')['files']
    for row in records:
        check_hash(archive / row['file'], row['sha256'])
    print(f'历史排版：{len(records)}份成品、源稿与维护依据原字节一致。')
    print('只核对版本和结构；不替代内容审校或实际放映。')


if __name__ == '__main__':
    try:
        verify()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'核对失败：{error}', file=sys.stderr)
        sys.exit(1)
