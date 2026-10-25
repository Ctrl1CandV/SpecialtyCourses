"""Package the reviewed 802 exams and record hashes for the final delivery."""
from __future__ import annotations

import hashlib
import json
import zipfile

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
    package = OUT / "六套试卷与答案.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as z:
        for p in range(1, 7):
            z.write(audit.student_pdf(p),
                    f"第{p}套/重邮802模拟试卷第{p}套.pdf")
            z.write(audit.answer_pdf(p),
                    f"第{p}套/重邮802模拟试卷第{p}套答案.pdf")
        z.writestr(
            "使用说明.txt",
            "2027考研重邮802数据结构六套模拟卷\n"
            "第1—3套保守，第4—6套适度创新。\n"
            "每套文件夹含一份试卷和一份对应参考答案，打印时请分别发放。\n"
            "试卷每套24题、150分、180分钟、19页；答案12页。\n"
            "题型分值为20/30/70/30，算法题为8/10/12分。\n"
            "参考答案允许等价正确解法，评分应结合实际实现。\n"
            "版本：2026-10-25，第6版题面及独立复核后的答案。\n",
        )
    audit.check_zip()

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
        "database_sha256": audit.sha(ROOT / "题库数据库/tiku.db"),
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
    write_json(OUT / "交付核对.json", manifest)
    print("Packaged 6 sets / 12 PDFs; provenance for 144 questions saved.")


if __name__ == "__main__":
    main()

