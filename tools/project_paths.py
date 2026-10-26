"""Shared project locations and resolution of dated evidence references.

Reviewed JSON sources retain their original bytes and provenance paths. The
relocation register resolves those historical references without rewriting the
reviewed question text or invalidating its existing content hashes.
"""
from pathlib import Path
import csv
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
COURSES = ROOT / '课程' / '课件'
MATERIALS = ROOT / '资料'
BANK = ROOT / '题库'
MOCK = ROOT / '试卷' / '六套模拟卷'
MOCK_SOURCE = MOCK / '源稿'
MOCK_OUTPUT = MOCK / '成品'
MOCK_AUDIT = MOCK / '审查'
MOCK_PLAN = MOCK / '命题依据'
PREDICTION = ROOT / '试卷' / '2026机构押题'

@lru_cache(maxsize=1)
def _relocations():
    with (ROOT / 'tools' / '目录迁移.csv').open(encoding='utf-8-sig', newline='') as f:
        return {r['old']: r['new'] for r in csv.DictReader(f) if r['new']}

def resolve_reference(reference, root=ROOT):
    """Resolve an existing or relocated path, keeping confinement checks intact."""
    root = Path(root).resolve()
    original = (root / reference).resolve()
    if not original.is_relative_to(root):
        return original  # Caller rejects it; never reinterpret ../ as an alias.
    if original.exists() or root != ROOT.resolve():
        return original
    old = Path(reference).as_posix()
    target = _relocations().get(old)
    return (root / target).resolve() if target else original
