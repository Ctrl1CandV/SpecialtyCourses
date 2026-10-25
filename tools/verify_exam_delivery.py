"""Verify the six reviewed exams and the packaged delivery."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "资料整理/六套模拟卷成稿"
PLAN = ROOT / "资料整理/六套模拟卷规划"
AUDIT = OUT / "审查记录"
REVIEWS = ((1, 2, "独立审查_第1至2套.json"),
           (3, 4, "独立审查_第3至4套.json"),
           (5, 6, "独立审查_第5至6套.json"))


def ensure(ok, message):
    if not ok:
        raise ValueError("交付核验失败：" + message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source(p):
    return OUT / f"试题源稿/第{p}套.json"


def answer(p):
    return OUT / f"答案源稿/第{p}套.json"


def student_pdf(p):
    return OUT / f"学生卷PDF/重邮802模拟试卷第{p}套.pdf"


def answer_pdf(p):
    return OUT / f"答案PDF/重邮802模拟试卷第{p}套答案.pdf"


def positions(p):
    for section, count, score in (("I", 4, 5), ("II", 10, 3), ("III", 7, 10)):
        for n in range(1, count + 1):
            yield f"S{p}-{section}{n:02}", section, n, score
    for n, score in enumerate((8, 10, 12), 1):
        yield f"S{p}-IV{n:02}", "IV", n, score


def hash_in(mapping, paper, suffix):
    ensure(isinstance(mapping, dict), f"第{paper}套审查哈希表缺失")
    if str(paper) in mapping:
        values = [mapping[str(paper)]]
    else:
        values = [v for k, v in mapping.items()
                  if k.replace("\\", "/").endswith(suffix)]
    ensure(len(values) == 1 and isinstance(values[0], str)
           and re.fullmatch(r"[0-9a-fA-F]{64}", values[0]),
           f"第{paper}套审查哈希缺失或重复：{suffix}")
    return values[0].lower()


def check_reviews():
    for start, end, filename in REVIEWS:
        report = read(AUDIT / filename)
        ids = {row[0] for p in range(start, end + 1) for row in positions(p)}
        rows = report.get("questions")
        ensure(isinstance(rows, list) and len(rows) == 48
               and {r.get("id") for r in rows} == ids,
               filename + " 缺题或题号重复")
        ensure(all(r.get("status") in ("pass", "content_pass") for r in rows),
               filename + " 有未通过题目")
        summary = report.get("summary", {})
        ensure(summary.get("question_count",
               summary.get("questions_reviewed", summary.get("reviewed_questions"))) == 48
               and summary.get("passed_questions", summary.get("content_pass")) == 48,
               filename + " 汇总通过数不足48")
        for key in ("unresolved_findings", "content_fail", "content_unresolved"):
            if key in summary:
                ensure(summary[key] in (0, []), filename + " 尚有未解决问题")
        visual = report.get("visual_pages")
        ensure(isinstance(visual, list) and len(visual) == 24
               and {(v.get("paper"), v.get("page")) for v in visual}
               == {(p, page) for p in range(start, end + 1)
                   for page in range(1, 13)}
               and all(v.get("status") == "pass" for v in visual),
               filename + " 答案页视觉审查不完整")
        for p in range(start, end + 1):
            for field, path, suffix in (
                ("source_hashes", source(p), f"试题源稿/第{p}套.json"),
                ("answer_hashes", answer(p), f"答案源稿/第{p}套.json"),
                ("pdf_hashes" if start == 5 else "answer_pdf_hashes",
                 answer_pdf(p), f"答案PDF/重邮802模拟试卷第{p}套答案.pdf"),
            ):
                ensure(hash_in(report.get(field), p, suffix) == sha(path),
                       filename + " 对应旧文件：" + str(path))
        if "figure_source_hash" in report:
            ensure(report["figure_source_hash"].lower()
                   == sha(OUT / "答案配图源稿.json"),
                   filename + " 对应旧答案配图")

    visual = read(AUDIT / "配图与学生页检查.json")
    pages = visual.get("visual_pages")
    ensure(visual.get("status") == "pass"
           and visual.get("student_pages_checked_this_round") == 14
           and isinstance(pages, list) and len(pages) == 14
           and len({(v.get("paper"), v.get("page")) for v in pages}) == 14
           and all(v.get("status") == "pass" for v in pages),
           "学生变动页/配图审查记录未通过或不足14页")
    for p in range(1, 7):
        ensure(hash_in(visual.get("student_source_hashes"), p, "") == sha(source(p))
               and hash_in(visual.get("student_pdf_hashes"), p, "") == sha(student_pdf(p)),
               f"第{p}套学生源稿/PDF与审查版本不同")
    ensure(visual.get("student_diagrams_source_sha256", "").lower()
           == sha(OUT / "配图源稿.json")
           and visual.get("answer_diagrams_source_sha256", "").lower()
           == sha(OUT / "答案配图源稿.json")
           and visual.get("student_diagram_count") == 12
           and visual.get("answer_diagram_count") == 25,
           "配图源稿或数量与审查版本不同")


def check_structure():
    blueprint = read(PLAN / "六套逐题蓝图.json")
    ids = [row[0] for p in range(1, 7) for row in positions(p)]
    ensure(isinstance(blueprint, list) and len(blueprint) == 144
           and len({b.get("id") for b in blueprint}) == 144
           and {b["id"] for b in blueprint} == set(ids),
           "蓝图不是144个唯一题号")
    by_id = {b["id"]: b for b in blueprint}
    content_hashes = {}
    texts = {"student": [], "answer": []}
    for p in range(1, 7):
        qdoc, adoc = read(source(p)), read(answer(p))
        qs, aa = qdoc.get("questions"), adoc.get("questions")
        ensure(qdoc.get("paper") == adoc.get("paper") == p
               and isinstance(qs, list) and isinstance(aa, list)
               and len(qs) == len(aa) == 24, f"第{p}套源稿/答案不是24题")
        for (qid, section, number, score), q, a in zip(positions(p), qs, aa):
            ensure(q.get("id") == a.get("id") == qid
                   and q.get("section") == section
                   and q.get("number") == number
                   and q.get("points") == score,
                   qid + " 题位、分值或答案ID错误")
            ensure(isinstance(q.get("content"), str) and q["content"].strip()
                   and isinstance(a.get("content"), str) and a["content"].strip(),
                   qid + " 题面或答案为空")
            digest = hashlib.sha256(q["content"].encode("utf-8")).hexdigest()
            ensure(by_id[qid].get("student_content_sha256") == digest,
                   qid + " 与蓝图题面哈希不符")
            content_hashes[qid] = digest
            refs, checks = a.get("references"), a.get("checks")
            ensure(isinstance(refs, list) and refs
                   and isinstance(checks, list) and checks
                   and all(isinstance(c, str) and c.strip() for c in checks),
                   qid + " 缺答案出处或验算记录")
            for ref in refs:
                ensure(isinstance(ref, dict) and isinstance(ref.get("path"), str)
                       and ref["path"].strip(), qid + " 参考路径为空")
                path = (ROOT / ref["path"]).resolve()
                ensure(path.is_relative_to(ROOT.resolve()) and path.is_file(),
                       qid + " 参考文件不存在：" + ref["path"])
            ensure(not re.search(r"Θ|紧渐近|TODO|待补齐", a["content"]),
                   qid + " 答案含未完成标记")
            prose = re.sub(r"\x60{3}.*?\x60{3}", "", a["content"], flags=re.S)
            ensure(prose.count("**") % 2 == 0, qid + " 粗体标记未闭合")
        for kind, path, count in (("student", student_pdf(p), 19),
                                  ("answer", answer_pdf(p), 12)):
            pages = [page.extract_text() or "" for page in PdfReader(path).pages]
            ensure(len(pages) == count, f"第{p}套{kind}PDF页数不符")
            text = "\n".join(pages)
            printed = [int(x) for x in re.findall(
                r"(?m)^\s*(\d+)[.．]\s*[（(]\d+分", text)]
            ensure(printed == [pos[2] for pos in positions(p)],
                   f"第{p}套{kind}PDF题号缺失或顺序错误")
            if kind == "student":
                ensure(not re.search(r"参考答案|评分建议|基本思想：", text),
                       f"第{p}套学生PDF出现答案提示")
            else:
                ensure(not re.search(r"\*\*(?:[\u3400-\u9fff（]|__\d)", text),
                       f"第{p}套答案PDF出现字面Markdown粗体标记")
            texts[kind].extend(pages)
    return content_hashes, texts


def check_build_records(content_hashes):
    student = read(OUT / "成卷结构核对.json")["papers"]
    answers = read(OUT / "答案成卷核对.json")
    ensure(len(student) == len(answers) == 6, "成卷记录未覆盖六套")
    for p, (s, a) in enumerate(zip(student, answers), 1):
        ensure(s.get("paper") == a.get("paper") == p
               and s.get("questions") == a.get("questions") == 24
               and s.get("points") == 150
               and s.get("pages") == 19 and a.get("pages") == 12
               and s.get("source_sha256", "").lower() == sha(source(p))
               and a.get("sha256", "").lower() == sha(answer_pdf(p)),
               f"第{p}套成卷记录与当前源稿/PDF不符")
    review = read(OUT / "内容复查核对.json")
    rows = review.get("questions")
    ensure(review.get("reviewed_questions") == 144
           and review.get("unresolved_findings") == 0
           and review.get("answers_visual_pages") == 72
           and review.get("student_pages_checked_this_round") == 14
           and isinstance(rows, list) and len(rows) == 144
           and {r.get("id") for r in rows} == set(content_hashes),
           "内容复查核对不完整")
    ensure(all(r.get("status") in ("pass", "content_pass")
               and r.get("question_sha256", "").lower()
               == content_hashes[r["id"]] for r in rows),
           "内容复查有未通过题目或旧题面哈希")
    for folder, expected in (("配图", 12), ("答案配图", 25)):
        png = {p.stem for p in (OUT / folder).glob("*.png")}
        svg = {p.stem for p in (OUT / folder).glob("*.svg")}
        ensure(len(png) == expected and svg == png,
               folder + " SVG/PNG数量或配对不符")


def artifact_files():
    files = set()
    for p in range(1, 7):
        files.update((source(p), answer(p), student_pdf(p), answer_pdf(p),
                      OUT / f"可编辑试题/第{p}套试卷.md",
                      OUT / f"可编辑答案/第{p}套答案.md"))
    files.update((OUT / "六套试卷与答案.zip",
                  OUT / "六套模拟试卷合订本.pdf",
                  OUT / "六套模拟试卷答案合订本.pdf",
                  OUT / "题型规范.json", OUT / "配图源稿.json",
                  OUT / "答案配图源稿.json",
                  OUT / "内容复查核对.json", OUT / "成卷结构核对.json",
                  OUT / "答案成卷核对.json",
                  PLAN / "六套逐题蓝图.json"))
    files.update(p for p in AUDIT.rglob("*") if p.is_file()
                 and p.suffix.lower() in {".json", ".zip", ".md"})
    files.update(p for name in ("配图", "答案配图")
                 for p in (OUT / name).rglob("*") if p.is_file()
                 and p.suffix.lower() in {".svg", ".png"})
    files.update(ROOT / "tools" / name for name in (
        "build_answer_figures.py", "build_exam_answers.py",
        "build_exam_papers.py", "exam_blueprint.py", "exam_figures.py",
        "package_exam_delivery.py", "verify_exam_delivery.py",
        "verify_exam_seeds.py"))
    return files


def check_inputs():
    hashes, texts = check_structure()
    check_reviews()
    check_build_records(hashes)
    return texts


def check_combined(texts):
    for kind, name in (("student", "六套模拟试卷合订本.pdf"),
                       ("answer", "六套模拟试卷答案合订本.pdf")):
        reader = PdfReader(OUT / name)
        ensure([page.extract_text() or "" for page in reader.pages] == texts[kind],
               name + " 与六份单套PDF页面不一致")
        titles = [getattr(x, "title", "") for x in reader.outline]
        ensure(len(titles) == 6
               and all(f"第{p}套" in titles[p - 1] for p in range(1, 7)),
               name + " 书签数量或顺序错误")


def check_zip():
    names = {f"第{p}套/重邮802模拟试卷第{p}套{suffix}.pdf"
             for p in range(1, 7) for suffix in ("", "答案")}
    names.add("使用说明.txt")
    with zipfile.ZipFile(OUT / "六套试卷与答案.zip") as z:
        listing = z.namelist()
        ensure(len(listing) == 13 and set(listing) == names
               and z.testzip() is None, "ZIP条目或CRC错误")
        ensure(z.read("使用说明.txt").strip(), "ZIP使用说明为空")
        for p in range(1, 7):
            for suffix, path in (("", student_pdf(p)), ("答案", answer_pdf(p))):
                name = f"第{p}套/重邮802模拟试卷第{p}套{suffix}.pdf"
                ensure(z.read(name) == path.read_bytes(),
                       f"ZIP第{p}套{suffix}不是现行PDF")


def check_manifest(manifest):
    ensure(manifest.get("version") == "2026-10-25-final-v6"
           and manifest.get("total_questions") == 144
           and manifest.get("total_points") == 900
           and manifest.get("student_total_pages") == 114
           and manifest.get("answer_total_pages") == 72
           and manifest.get("student_diagrams") == 12
           and manifest.get("answer_diagrams") == 25,
           "交付清单版本或总量错误")
    rows = manifest.get("papers")
    ensure(isinstance(rows, list) and len(rows) == 6, "交付清单缺六套记录")
    for p, row in enumerate(rows, 1):
        ensure(row.get("paper") == p and row.get("questions") == 24
               and row.get("points") == 150
               and row.get("student_pages") == 19
               and row.get("answer_pages") == 12
               and row.get("student_source_sha256") == sha(source(p))
               and row.get("answer_source_sha256") == sha(answer(p)),
               f"第{p}套交付清单哈希或页数错误")
    ensure(manifest.get("database_sha256") == sha(ROOT / "题库数据库/tiku.db"),
           "题库数据库哈希与清单不同")
    actual = {p.relative_to(ROOT).as_posix(): p for p in artifact_files()}
    listed = manifest.get("artifacts")
    ensure(isinstance(listed, dict) and set(listed) == set(actual),
           "交付清单工件列表缺失或多出文件")
    for name, path in actual.items():
        ensure(listed[name] == sha(path), "工件哈希不符：" + name)


def main():
    texts = check_inputs()
    check_combined(texts)
    check_zip()
    check_manifest(read(OUT / "交付核对.json"))
    print("PASS final: 144题900分、114页学生卷和72页答案；审查、合订本、ZIP及全部工件哈希一致。")


if __name__ == "__main__":
    main()

