"""Validate and write the two formal answer-source JSON files."""

import json
from pathlib import Path

from paper5_answers import ANSWERS as PAPER5
from paper6_answers import ANSWERS as PAPER6


ROOT = Path(__file__).resolve().parents[3]
QUESTION_DIR = ROOT / "资料整理/六套模拟卷成稿/试题源稿"
ANSWER_DIR = ROOT / "资料整理/六套模拟卷成稿/答案源稿"
VERSION = "2026-10-25-answer-v1"


def build(paper, authored):
    source = json.loads((QUESTION_DIR / f"第{paper}套.json").read_text(encoding="utf-8"))
    question_ids = [q["id"] for q in source["questions"]]
    if len(question_ids) != 24 or set(question_ids) != set(authored):
        raise ValueError(f"paper {paper}: ID mismatch")
    rows = []
    for q in source["questions"]:
        qid = q["id"]
        a = authored[qid]
        if not a["content"].strip() or not isinstance(a["checks"], list) or not a["checks"]:
            raise ValueError(f"{qid}: empty answer/check")
        if not isinstance(a["references"], list) or not a["references"]:
            raise ValueError(f"{qid}: empty references")
        for r in a["references"]:
            if set(r) != {"path", "location", "use"}:
                raise ValueError(f"{qid}: reference schema")
            if not (ROOT / r["path"]).is_file():
                raise FileNotFoundError(f"{qid}: {r['path']}")
        section = q["section"]
        if section == "I":
            if "填空" not in a["content"]:
                raise ValueError(f"{qid}: missing per-blank answer")
            numbers = sorted(set(int(x) for x in __import__("re").findall(r"__(\d+)__", q["content"])))
            if not all(f"__{number}__" in a["content"] for number in numbers):
                raise ValueError(f"{qid}: missing some blank labels")
        elif section == "II" and "__1__" not in a["content"]:
            raise ValueError(f"{qid}: missing fill answer")
        elif section == "III":
            for part in __import__("re").findall(r"（(\d+)）（\d+分）", q["content"]):
                if f"（{part}）" not in a["content"]:
                    raise ValueError(f"{qid}: missing subanswer {part}")
        elif section == "IV":
            required = ("基本思想", "C语言实现", "复杂度", f"建议评分（{q['points']}分）")
            if not all(heading in a["content"] for heading in required):
                raise ValueError(f"{qid}: incomplete algorithm answer")
            if a["content"].count(chr(96) * 3 + "c") != 1:
                raise ValueError(f"{qid}: missing one C implementation")
        rows.append({"id": qid, **a})
    output = {"paper": paper, "version": VERSION, "questions": rows}
    ANSWER_DIR.mkdir(parents=True, exist_ok=True)
    target = ANSWER_DIR / f"第{paper}套.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{target}: {len(rows)} answers")


build(5, PAPER5)
build(6, PAPER6)
