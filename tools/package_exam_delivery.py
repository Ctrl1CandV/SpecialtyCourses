"""Package the reviewed 802 exams and record hashes for the final delivery."""
from __future__ import annotations

import hashlib
import json

try:
    from . import verify_exam_delivery as audit
except ImportError:
    import verify_exam_delivery as audit

ROOT = audit.ROOT
OUT = audit.OUT
PLAN = audit.PLAN
AUDIT = audit.AUDIT


def content_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    # All review and source/PDF bindings must pass before any final output changes.
    texts = audit.check_inputs()
    audit.check_combined(texts)

    blueprint = {row["id"]: row for row in audit.read(PLAN / "六套逐题蓝图.json")}
    traces = []
    reports = []
    for p in range(1, 7):
        questions = audit.read(audit.source(p))["questions"]
        answers = audit.read(audit.answer(p))["questions"]
        for q, answer in zip(questions, answers):
            b = blueprint[q["id"]]
            traces.append({
                "id": q["id"],
                "title": b["title"],
                "points": q["points"],
                "chapter": b["chapter"],
                "profile": b["paper_profile"],
                "innovation": b["innovation"],
                "question_sha256": content_sha(q["content"]),
                "answer_sha256": content_sha(answer["content"]),
                "question_reference": b["reference_alignment"],
                "answer_references": answer["references"],
                "verification_notes": answer["checks"],
                "revision_note": b["revision_note"],
            })
        reports.append({
            "paper": p,
            "questions": 24,
            "points": 150,
            "student_pages": 19,
            "answer_pages": 12,
            "student_source_sha256": audit.sha(audit.source(p)),
            "answer_source_sha256": audit.sha(audit.answer(p)),
        })
    audit.ensure(len(traces) == 144 and len({r["id"] for r in traces}) == 144,
                 "逐题溯源不是144个唯一题号")

    write_json(AUDIT / "逐题溯源.json",
               {"version": "2026-10-25-final-v6", "questions": traces})

    artifacts = audit.artifact_files()
    audit.ensure(all(path.is_file() for path in artifacts),
                 "交付清单存在缺失文件")
    manifest = {
        "version": "2026-10-25-final-v6",
        "status": "独立内容复核及最终视觉检查完成",
        "papers": reports,
        "total_questions": 144,
        "total_points": 900,
        "student_diagrams": 12,
        "answer_diagrams": 25,
        "student_total_pages": 114,
        "answer_total_pages": 72,
        "database_sha256": audit.sha(ROOT / "题库/tiku.db"),
        "artifacts": {
            path.relative_to(ROOT).as_posix(): audit.sha(path)
            for path in sorted(artifacts)
        },
        "limitations": [
            "难度与用时为命题目标和编辑估计，尚未经过考生限时实测。",
            "历年资料为回忆修订资料；错误参考答案以独立验算和现行题意为准。",
        ],
    }
    audit.check_manifest(manifest)
    write_json(OUT / "审查/交付核对.json", manifest)
    print("Registered 6 sets / 12 PDFs; provenance for 144 questions saved. No ZIP is created.")


if __name__ == "__main__":
    main()

