#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and render the six 802 mock-exam blueprints.

The editable source is 资料整理/六套模拟卷规划/六套逐题蓝图.json.
Everything rendered by this command is a projection.  The command never writes
to tiku.db.  Run without arguments to check projections, or --write to update
them after the source has passed validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "资料整理" / "六套模拟卷规划"
DB = ROOT / "题库数据库" / "tiku.db"
SOURCE = PLAN / "六套逐题蓝图.json"
OLD_SOURCE = PLAN / "历史版本" / "2026-10-20" / "六套逐题蓝图.json"
OLD_VERIFY = PLAN / "历史版本" / "2026-10-20" / "蓝图数据复核.json"

FORMAT = json.loads((ROOT/'资料整理/六套模拟卷成稿/题型规范.json').read_text(encoding='utf-8'))
SECTION_NAMES = {key: value['name'] for key,value in FORMAT['sections'].items()}
SECTION_COUNTS = {key: value['count'] for key,value in FORMAT['sections'].items()}
SECTION_POINTS = {key: sum(value['points']) for key,value in FORMAT['sections'].items()}
CHAPTERS = [
    "绪论", "线性表", "栈队列", "串", "数组广义表",
    "树", "图", "查找", "排序",
]
MODES = {"选用", "改编", "原创"}
LEVELS = {"基", "中", "辨"}
NOVELTY_TYPES = {
    "基础锚点", "平行练习", "约束变化", "表示转换",
    "逆向推断", "错解诊断", "目标变化", "条件辨析",
}
TASK_FAMILIES = {
    "复杂度分析", "过程追踪", "结构构造", "表示转换", "逆向推断",
    "错误诊断", "条件辨析", "性能比较", "状态维护", "算法设计", "代码补全", "数量计算", "结构推断",
}
NEW_TEXT_FIELDS = (
    "objective", "evidence_required", "misconception", "transfer",
    "task_family", "novelty_type", "time_reason", "revision_note", "reference_alignment",
)
REQUIRED_FIELDS = (
    "id", "paper", "section", "number", "title", "mode", "chapter",
    "tags", "points", "minutes", "level", "task", "data",
    "answer_blueprint", "source_ids", "history_ids", "change",
    "rubric", "scope", "exposure",
) + NEW_TEXT_FIELDS
ID_RE = re.compile(r"^S([1-6])-(I|II|III|IV)(\d{2})$")
GENERIC_RUBRICS = {
    (("思想", 2), ("实现", 4), ("分析", 2)),
    (("思想", 2), ("实现", 5), ("正确性", 1), ("复杂度", 2)),
    (("思想", 2), ("实现", 6), ("正确性", 2), ("复杂度", 2)),
    (("功能或输出", 2), ("代码空或关键依据", 2), ("复杂度或边界", 1)),
}
BT = chr(96)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def csv_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def design_hash(item: dict) -> str:
    """Fingerprint only the data and claims covered by the old seed checks."""
    value = {
        field: item.get(field, "")
        for field in ("task", "data", "answer_blueprint")
    }
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def legacy_applicability(current: list[dict], old: list[dict],
                         validations: list[dict]) -> dict:
    current_by_id = {item["id"]: item for item in current}
    old_by_id = {item["id"]: item for item in old}
    records = []
    per_item = defaultdict(list)
    for index, validation in enumerate(validations, start=1):
        ids = validation.get("items", [])
        details = []
        for item_id in ids:
            before = old_by_id.get(item_id)
            after = current_by_id.get(item_id)
            old_hash = design_hash(before) if before else None
            new_hash = design_hash(after) if after else None
            if before is None and after is None and item_id.startswith("备用"):
                state = "备用项_不属主卷"
            elif before is None or after is None:
                state = "无法对应"
            elif old_hash == new_hash:
                state = "旧设计未变"
            else:
                state = "设计已变"
            details.append({
                "题位": item_id,
                "状态": state,
                "旧设计哈希": old_hash,
                "现设计哈希": new_hash,
            })
            per_item[item_id].append(state)
        if any(d["状态"] == "无法对应" for d in details):
            status = "无法对应"
        elif details and all(d["状态"] == "备用项_不属主卷" for d in details):
            status = "备用项_不属主卷"
        elif any(d["状态"] == "设计已变" for d in details):
            status = "旧结果失效待复核"
        else:
            status = "旧设计未变_结果可追溯"
        records.append({
            "序号": index,
            "题位": ids,
            "核算内容": validation.get("name", ""),
            "旧结果": validation.get("result"),
            "状态": status,
            "逐题对照": details,
        })
    item_status = {}
    for item in current:
        states = per_item.get(item["id"], [])
        if not states:
            label = "旧复核未覆盖"
        elif "无法对应" in states:
            label = "无法对应"
        elif "设计已变" in states:
            label = "旧复核失效待重算"
        else:
            label = "旧设计未变_旧结果可追溯"
        item_status[item["id"]] = label
    return {
        "说明": (
            "本文件只对照2026-10-20旧版题位的任务、数据、答案蓝图哈希。"
            "旧设计未变表示旧结果仍对应相同设计，不表示本工具重新验算，"
            "也不表示已形成成品标准答案。"
        ),
        "旧核算项": len(records),
        "状态统计": dict(Counter(r["状态"] for r in records)),
        "逐题状态": item_status,
        "核算项": records,
    }


def safe_reference(root: Path, reference: str) -> bool:
    """Only accept an existing repo-local path, optionally with a fragment."""
    if not isinstance(reference, str) or not reference.strip():
        return False
    path_part = reference.split("#", 1)[0]
    if not path_part or "://" in path_part:
        return False
    path = Path(path_part)
    if path.is_absolute():
        return False
    root_resolved = root.resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError:
        return False
    return target.exists()


def rubric_errors(item: dict) -> list[str]:
    rubric = item.get("rubric")
    if not isinstance(rubric, list) or not rubric:
        return ["评分骨架须为非空二维数组"]
    errors = []
    total = 0
    normalized = []
    labels = set()
    for part in rubric:
        if (not isinstance(part, list) or len(part) != 2
                or not isinstance(part[0], str)
                or not part[0].strip()
                or not isinstance(part[1], int)
                or isinstance(part[1], bool)
                or part[1] <= 0):
            errors.append("评分项须为[具体评分点,正整数分值]")
            continue
        label = part[0].strip()
        if label in labels:
            errors.append("评分项名称重复: " + label)
        labels.add(label)
        normalized.append((label, part[1]))
        total += part[1]
    if isinstance(item.get("points"), int) and total != item["points"]:
        errors.append("评分骨架合计与题目分值不符")
    if tuple(normalized) in GENERIC_RUBRICS:
        errors.append("仍使用旧的通用评分模板，须写可核对的本题评分点")
    return errors


def integer_value(value) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def load_database(path: Path) -> tuple[dict[str, dict], int]:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT id, source, source_detail, stem, answer, notes "
            "FROM questions"
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}, len(rows)
    finally:
        connection.close()


def validate(items: list[dict], db_rows: dict[str, dict],
             root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(items, list):
        return ["蓝图JSON顶层必须为数组"], warnings
    if len(items) != 144:
        errors.append("蓝图须有144道题，实际: " + str(len(items)))
    ids = set()
    seen_slots = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append("第" + str(index) + "项不是对象")
            continue
        label = str(item.get("id", "第" + str(index) + "项"))
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(label + ": 缺字段 " + field)
        if any(field not in item for field in REQUIRED_FIELDS):
            continue
        match = ID_RE.fullmatch(str(item["id"]))
        if match is None:
            errors.append(label + ": 题位ID格式错误")
        elif (int(match.group(1)), match.group(2), int(match.group(3))) != (
                item["paper"], item["section"], item["number"]):
            errors.append(label + ": ID与paper/section/number不一致")
        if label in ids:
            errors.append(label + ": 题位ID重复")
        ids.add(label)
        slot = (item["paper"], item["section"], item["number"])
        if all(isinstance(part, (str, int)) for part in slot):
            if slot in seen_slots:
                errors.append(label + ": 套卷题号重复")
            seen_slots.add(slot)
        if item["paper"] not in range(1, 7):
            errors.append(label + ": paper应为1到6")
        if item["section"] not in SECTION_COUNTS:
            errors.append(label + ": section无效")
        if not isinstance(item["mode"], str) or item["mode"] not in MODES:
            errors.append(label + ": mode无效")
        if not isinstance(item["chapter"], str) or item["chapter"] not in CHAPTERS:
            errors.append(label + ": 主章节无效")
        if not isinstance(item["level"], str) or item["level"] not in LEVELS:
            errors.append(label + ": 难度设计标签无效")
        if (not isinstance(item["novelty_type"], str)
                or item["novelty_type"] not in NOVELTY_TYPES):
            errors.append(label + ": novelty_type不在8类中")
        if (not isinstance(item["task_family"], str)
                or item["task_family"] not in TASK_FAMILIES):
            errors.append(label + ": task_family不在约定的作答动作中")
        for field in ("title", "task", "answer_blueprint", "change", "scope") + NEW_TEXT_FIELDS:
            if not isinstance(item[field], str) or not item[field].strip():
                errors.append(label + ": " + field + "须为非空文本")
        if not isinstance(item["data"], str):
            errors.append(label + ": data须为文本，可为空")
        if (not isinstance(item["points"], int)
                or isinstance(item["points"], bool) or item["points"] <= 0):
            errors.append(label + ": points须为正整数")
        if (not isinstance(item["minutes"], int)
                or isinstance(item["minutes"], bool) or item["minutes"] <= 0):
            errors.append(label + ": minutes须为正整数")
        section = item["section"]
        if section == "I" and item["points"] != 5:
            errors.append(label + ": 程序阅读须5分")
        elif section == "II" and item["points"] != 3:
            errors.append(label + ": 填空须3分")
        elif section == "III" and item["points"] != 10:
            errors.append(label + ": 综合应用须10分")
        elif section == "IV" and item["number"] in (1, 2, 3):
            if item["points"] != {1: 8, 2: 10, 3: 12}[item["number"]]:
                errors.append(label + ": 算法分值须依次为8/10/12")
        if (not isinstance(item["tags"], list) or not item["tags"]
                or any(not isinstance(tag, str) or not tag.strip()
                       for tag in item["tags"])):
            errors.append(label + ": tags须为非空文本数组")
        for field in ("source_ids", "history_ids"):
            values = item[field]
            if not isinstance(values, list):
                errors.append(label + ": " + field + "须为数组")
                continue
            if len(values) != len(set(map(str, values))):
                errors.append(label + ": " + field + "内部重复")
            for source_id in values:
                if not isinstance(source_id, str) or source_id not in db_rows:
                    errors.append(label + ": " + field + "所引题库ID不存在: " + str(source_id))
        if item["mode"] in {"选用", "改编"} and not item["source_ids"]:
            errors.append(label + ": 选用/改编须有直接来源")
        if item["mode"] == "原创" and item["source_ids"]:
            errors.append(label + ": 原创题不可填直接来源；方法锚点放history_ids")
        if not item["history_ids"]:
            warnings.append(label + ": 无重邮历史锚点，需在设计中说明选题理由")
        if not isinstance(item.get("innovation"), bool):
            errors.append(label + ": innovation须明确标记为布尔值")
        if item["paper"] <= 3 and item.get("innovation"):
            errors.append(label + ": 保守卷不得安排明确拓展题位")
        if item["paper"] <= 3 and not item["history_ids"]:
            errors.append(label + ": 保守卷须有近三年802任务依据")
        for ref_id in item["source_ids"] + item["history_ids"]:
            if not re.match(r"^真题-202[456]-", ref_id):
                errors.append(label + ": 本轮强参考仅采用2024—2026重邮802，其他线索移入辅助备注")
        errors.extend(label + ": " + problem for problem in rubric_errors(item))
        exposure = item["exposure"]
        if not isinstance(exposure, dict):
            errors.append(label + ": exposure须为对象")
        else:
            if not isinstance(exposure.get("status"), str) or not exposure["status"].strip():
                errors.append(label + ": exposure.status须为非空文本")
            refs = exposure.get("references")
            if not isinstance(refs, list):
                errors.append(label + ": exposure.references须为路径数组")
            else:
                for ref in refs:
                    if not safe_reference(root, ref):
                        errors.append(label + ": 曝光引用路径不存在或越界: " + str(ref))
            if not isinstance(exposure.get("response"), str) or not exposure["response"].strip():
                errors.append(label + ": exposure.response须为非空文本")
        if isinstance(item["source_ids"], list):
            for source_id in item["source_ids"]:
                row = db_rows.get(source_id) if isinstance(source_id, str) else None
                if row and not (row["answer"] or "").strip():
                    warnings.append(label + ": 直接来源暂无库内答案，成稿须独立核答")
    for paper in range(1, 7):
        group = [item for item in items if isinstance(item, dict)
                 and item.get("paper") == paper]
        if len(group) != 24:
            errors.append("第" + str(paper) + "套须24题")
        innovation_cap = FORMAT.get("content_policy", {}).get("innovation_slot_caps", {}).get(str(paper), 4)
        if sum(bool(item.get("innovation")) for item in group) > innovation_cap:
            errors.append("第" + str(paper) + "套明确拓展题位超过本轮" + str(innovation_cap) + "题编辑上限")
        if sum(integer_value(item.get("points")) for item in group) != 150:
            errors.append("第" + str(paper) + "套须150分")
        for section, expected_count in SECTION_COUNTS.items():
            sub = [item for item in group if item.get("section") == section]
            if len(sub) != expected_count:
                errors.append("第" + str(paper) + "套" + section
                              + "题数应为" + str(expected_count))
            if sum(integer_value(item.get("points")) for item in sub) != SECTION_POINTS[section]:
                errors.append("第" + str(paper) + "套" + section + "分值不符")
            expected_nums = set(range(1, expected_count + 1))
            if {item.get("number") for item in sub} != expected_nums:
                errors.append("第" + str(paper) + "套" + section + "题号不连续")
        minutes = sum(integer_value(item.get("minutes")) for item in group)
        if minutes > 180:
            errors.append("第" + str(paper) + "套预计作答"
                          + str(minutes) + "分钟，超过180分钟考试时长")
        elif minutes >= 170:
            warnings.append("第" + str(paper) + "套预计仅留"
                            +str(180-minutes)+"分钟复查；代码扩充后须限时试做核实负担")
        chapter_points = Counter()
        for item in group:
            chapter_points[item.get("chapter")] += integer_value(item.get("points"))
        for chapter in CHAPTERS:
            if chapter_points[chapter] == 0:
                warnings.append("第" + str(paper) + "套主章节未覆盖: " + chapter)
    exact_tasks = defaultdict(list)
    repeated_data = defaultdict(list)
    source_usage = defaultdict(list)
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            continue
        task = item.get("task")
        if isinstance(task, str) and task.strip():
            exact_tasks["".join(task.split())].append(item["id"])
        data = item.get("data")
        if isinstance(data, str) and len(data.strip()) >= 20:
            repeated_data["".join(data.split())].append(item["id"])
        if isinstance(item.get("source_ids"), list):
            for source_id in item["source_ids"]:
                if isinstance(source_id, str):
                    source_usage[source_id].append(item["id"])
    for ids_for_task in exact_tasks.values():
        if len(ids_for_task) > 1:
            errors.append("题位存在相同任务文本: " + "、".join(ids_for_task))
    for ids_for_data in repeated_data.values():
        if len(ids_for_data) > 1:
            warnings.append("题位复用同一较长数据: " + "、".join(ids_for_data))
    for source_id, ids_for_source in source_usage.items():
        if len(ids_for_source) >= 4:
            warnings.append(
                "同一直接来源使用" + str(len(ids_for_source)) + "次: "
                + source_id + " → " + "、".join(ids_for_source)
            )
    return errors, warnings


def source_audit(items: list[dict], db_rows: dict[str, dict],
                 db_count: int, db_path: Path) -> dict:
    direct = defaultdict(list)
    historical = defaultdict(list)
    for item in items:
        for source_id in item["source_ids"]:
            direct[source_id].append(item["id"])
        for source_id in item["history_ids"]:
            if item["id"] not in direct[source_id]:
                historical[source_id].append(item["id"])
    records = []
    for source_id in sorted(set(direct) | set(historical)):
        row = db_rows[source_id]
        evidence = {
            "id": source_id,
            "source": row["source"],
            "source_detail": row["source_detail"] or "",
            "stem": row["stem"],
            "answer_present": bool((row["answer"] or "").strip()),
            "notes": row["notes"] or "",
            "usage": sorted(direct[source_id]),
            "historical_only": sorted(historical[source_id]),
        }
        records.append(evidence)
    return {
        "metadata": {
            "说明": (
                "本表完整摘录题库原题题干与出处，仅支持来源追溯。"
                "它不是现设计任务或答案的验算，也不能证明学生实际见过该题。"
            ),
            "题库题数": db_count,
            "题库文件SHA256": hashlib.sha256(db_path.read_bytes()).hexdigest(),
            "引用原题数": len(records),
            "题干截断": False,
        },
        "records": records,
    }


def csv_projection(items: list[dict]) -> bytes:
    headers = [
        "id", "paper", "section", "number", "points", "title", "mode",
        "chapter", "tags", "task", "data", "answer_blueprint",
        "source_ids", "history_ids", "change", "level", "minutes",
        "rubric", "scope",
        *NEW_TEXT_FIELDS, "exposure_status", "exposure_references",
        "exposure_response",
    ]
    rows = []
    for item in items:
        row = []
        for field in headers:
            if field == "tags":
                value = "；".join(item["tags"])
            elif field in ("source_ids", "history_ids"):
                value = "；".join(item[field])
            elif field == "rubric":
                value = "；".join(str(label) + ":" + str(points)
                                  for label, points in item["rubric"])
            elif field.startswith("exposure_"):
                key = field[len("exposure_"):]
                value = item["exposure"][key]
                if key == "references":
                    value = "；".join(value)
            else:
                value = item[field]
            row.append(value)
        rows.append(row)
    return csv_bytes(headers, rows)


def chapter_matrix(items: list[dict]) -> bytes:
    headers = ["主章节"] + ["第" + str(p) + "套" for p in range(1, 7)] + ["六套合计"]
    rows = []
    for chapter in CHAPTERS:
        values = [
            sum(item["points"] for item in items
                if item["paper"] == paper and item["chapter"] == chapter)
            for paper in range(1, 7)
        ]
        rows.append([chapter, *values, sum(values)])
    rows.append(["合计", *[150] * 6, 900])
    return csv_bytes(headers, rows)


def coverage_matrix(items: list[dict]) -> bytes:
    headers = [
        "考点", *["第" + str(p) + "套题号" for p in range(1, 7)],
        "覆盖套数", "综合/算法深覆盖套数",
    ]
    tags = sorted({tag for item in items for tag in item["tags"]})
    rows = []
    for tag in tags:
        by_paper = [
            [item["id"] for item in items
             if item["paper"] == paper and tag in item["tags"]]
            for paper in range(1, 7)
        ]
        deep = sum(
            any(item["paper"] == paper and item["section"] in ("III", "IV")
                and tag in item["tags"] for item in items)
            for paper in range(1, 7)
        )
        rows.append([
            tag, *["；".join(ids) for ids in by_paper],
            sum(bool(ids) for ids in by_paper), deep,
        ])
    return csv_bytes(headers, rows)


def task_matrix(items: list[dict]) -> bytes:
    headers = [
        "维度", "类别", *["第" + str(p) + "套题数" for p in range(1, 7)],
        "六套题数", "六套分值",
    ]
    rows = []
    for field, dimension in (("task_family", "任务方式"),
                             ("novelty_type", "创新类型")):
        values = sorted({item[field] for item in items})
        for value in values:
            counts = [
                sum(item["paper"] == paper and item[field] == value
                    for item in items)
                for paper in range(1, 7)
            ]
            rows.append([
                dimension, value, *counts, sum(counts),
                sum(item["points"] for item in items if item[field] == value),
            ])
    return csv_bytes(headers, rows)


def revision_matrix(items: list[dict], old: list[dict]) -> bytes:
    before = {item["id"]: item for item in old}
    headers = [
        "题位", "变化状态", "旧标题", "现标题", "旧处理", "现处理",
        "旧主章", "现主章", "旧分值", "现分值", "旧任务", "现任务",
        "旧答案蓝图", "现答案蓝图", "修订说明",
    ]
    rows = []
    for item in items:
        prior = before.get(item["id"], {})
        if not prior:
            status = "新增题位"
        elif design_hash(prior) != design_hash(item):
            status = "任务或答案变化"
        elif any(prior.get(key) != item.get(key)
                 for key in ("title", "mode", "chapter", "points", "minutes",
                             "level", "rubric", "scope")):
            status = "定位或评分调整"
        else:
            status = "补充设计审查字段"
        rows.append([
            item["id"], status, prior.get("title", ""), item["title"],
            prior.get("mode", ""), item["mode"],
            prior.get("chapter", ""), item["chapter"],
            prior.get("points", ""), item["points"],
            prior.get("task", ""), item["task"],
            prior.get("answer_blueprint", ""), item["answer_blueprint"],
            item["revision_note"],
        ])
    return csv_bytes(headers, rows)


def summary_report(items: list[dict], db_rows: dict[str, dict],
                   db_count: int, warnings: list[str],
                   legacy: dict) -> dict:
    papers = {}
    for paper in range(1, 7):
        group = [item for item in items if item["paper"] == paper]
        modes = {
            mode: {
                "题数": sum(item["mode"] == mode for item in group),
                "分值": sum(item["points"] for item in group if item["mode"] == mode),
            }
            for mode in ("选用", "改编", "原创")
        }
        chapters = {
            chapter: sum(item["points"] for item in group if item["chapter"] == chapter)
            for chapter in CHAPTERS
        }
        levels = {
            level: sum(item["points"] for item in group if item["level"] == level)
            for level in ("基", "中", "辨")
        }
        source_points = sum(
            item["points"] for item in group
            if any((db_rows[source_id]["source"] or "").startswith("真题")
                   for source_id in item["source_ids"])
        )
        papers[str(paper)] = {
            "题数": len(group),
            "总分": sum(item["points"] for item in group),
            "预计作答分钟": sum(item["minutes"] for item in group),
            "预计复查分钟": 180 - sum(item["minutes"] for item in group),
            "套卷定位": "保守卷" if paper <= 3 else "适度创新卷",
            "明确拓展题位": [item["id"] for item in group if item.get("innovation")],
            "明确拓展分值": sum(item["points"] for item in group if item.get("innovation")),
            "处理方式": modes,
            "主章节分值": chapters,
            "难度目标分值": levels,
            "直接取用或改编重邮题的分值": source_points,
            "任务方式题数": dict(Counter(item["task_family"] for item in group)),
            "创新类型题数": dict(Counter(item["novelty_type"] for item in group)),
        }
    all_source_points = sum(p["直接取用或改编重邮题的分值"] for p in papers.values())
    source_usage = defaultdict(list)
    for item in items:
        for source_id in item["source_ids"]:
            source_usage[source_id].append(item["id"])
    return {
        "说明": (
            "以下为蓝图结构检查与设计标签统计；时间及难度均未经过考生试测。"
            "来源ID存在不等于当前题面、答案、评分细则已经验算。"
        ),
        "生成工具": "tools/exam_blueprint.py",
        "蓝图题数": len(items),
        "蓝图总分": sum(item["points"] for item in items),
        "题库题数": db_count,
        "直接取用或改编重邮题的分值": all_source_points,
        "来源统计口径": "一题有多个重邮直接来源时只计该题分值一次；历史锚点不计入",
        "旧复核适用性统计": legacy["状态统计"],
        "重复直接来源": [
            {"来源ID": source_id, "使用题位": ids}
            for source_id, ids in sorted(source_usage.items())
            if len(ids) > 1
        ],
        "各套": papers,
        "警告": warnings,
    }


def md_item(item: dict, legacy_status: str) -> list[str]:
    revisions = list(dict.fromkeys(
        item[field].strip().rstrip("。；")
        for field in ("change", "revision_note") if item[field].strip()
    ))
    lines = [
        "#### " + item["id"] + " " + item["title"] + "（"
        + str(item["points"]) + "分，" + item["mode"] + "）",
        "",
        "**能力目标：** " + item["objective"],
        "",
        "**具体任务：** " + item["task"],
        "",
    ]
    if item["data"]:
        lines += ["**数据与约定：** " + item["data"], ""]
    lines += [
        "**必须提交的证据：** " + item["evidence_required"],
        "",
        "**答案蓝图：** " + item["answer_blueprint"],
        "",
        "**易错思路：** " + item["misconception"],
        "",
        "**迁移点：** " + item["transfer"],
        "",
        "**任务方式与变式手段：** " + item["task_family"]
        + "；" + item["novelty_type"] + "。",
        "",
        "**本轮分层：** " + ("明确拓展题位" if item.get("innovation") else "真题同型或同方法小幅迁移")
        + "；" + item["reference_alignment"],
        "",
        "**参考评分：** " + "；".join(
            label + str(points) + "分" for label, points in item["rubric"]
        ) + "。",
        "",
        "**预计耗时：** " + str(item["minutes"]) + "分钟；"
        + item["time_reason"],
        "",
        "**直接来源：** " + (
            "、".join(BT + source_id + BT for source_id in item["source_ids"])
            if item["source_ids"] else "项目独立设计，无直接题面来源"
        ) + "。",
        "",
        "**历史方法锚点：** " + (
            "、".join(BT + source_id + BT for source_id in item["history_ids"])
            if item["history_ids"] else "无；见选题理由"
        ) + "。",
        "",
        "**处理与修订：** " + "；".join(revisions) + "。",
        "",
        "**学生接触状态：** " + item["exposure"]["status"]
        + "；" + item["exposure"]["response"],
        "",
        "**接触依据路径：** " + (
            "、".join(BT + path + BT for path in item["exposure"]["references"])
            if item["exposure"]["references"] else "未列路径"
        ) + "。路径仅指仓库材料，实际发放/授课需另行核实。",
        "",
        "**范围状态与考点：** " + item["scope"] + "；"
        + "、".join(item["tags"]) + "。",
        "",
        "**旧种子复核状态：** " + legacy_status + "。",
        "",
    ]
    return lines


def paper_md(items: list[dict], paper: int, legacy: dict) -> bytes:
    group = [item for item in items if item["paper"] == paper]
    minutes = sum(item["minutes"] for item in group)
    counts = Counter(item["mode"] for item in group)
    points = {
        mode: sum(item["points"] for item in group if item["mode"] == mode)
        for mode in ("选用", "改编", "原创")
    }
    lines = [
        "# 第" + str(paper) + "套逐题设计蓝图",
        "",
        "> 2027重邮802备考规划。每套24题、150分；此文是题面、答案与评分的设计，"
        "尚非已验算完成的成品试卷。",
        "",
        "预计作答" + str(minutes) + "分钟，留"
        + str(180 - minutes) + "分钟复查；时间是设计估计，需试做校准。",
        "",
        "来源构成：选用" + str(counts["选用"]) + "题/"
        + str(points["选用"]) + "分；改编" + str(counts["改编"])
        + "题/" + str(points["改编"]) + "分；原创"
        + str(counts["原创"]) + "题/" + str(points["原创"]) + "分。",
        "",
        "仓库课件路径只能证明材料存在；是否已向学生讲授或发放，须查实际记录。",
        "",
        "## 卷面一览",
        "",
        "| 题位 | 分值 | 主题 | 处理 | 主章 | 任务方式 | 创新类型 | 难度目标 | 预计分钟 |",
        "|---|---:|---|---|---|---|---|---|---:|",
    ]
    for item in group:
        lines.append(
            "| " + item["id"] + " | " + str(item["points"]) + " | "
            + item["title"] + " | " + item["mode"] + " | "
            + item["chapter"] + " | " + item["task_family"] + " | "
            + item["novelty_type"] + " | " + item["level"]
            + " | " + str(item["minutes"]) + " |"
        )
    lines += ["", "## 逐题设计", ""]
    for section, section_name in SECTION_NAMES.items():
        lines += ["### " + section_name, ""]
        for item in group:
            if item["section"] == section:
                lines += md_item(item, legacy["逐题状态"][item["id"]])
    lines += [
        "## 成稿前核对",
        "",
        "- 当前答案为蓝图，成稿须逐题补全题面、图表、选项与标准答案，并独立验算。",
        "- 程序阅读以代码补全为主；填空须核对空数、约定与可判定结果；算法须核对边界、复杂度与给分依据。",
        "- 旧种子复核适用性见" + BT + "旧复核适用性.json" + BT
        + "；题位设计变化后不得沿用旧结果。",
        "- 难度是设计标签，预计耗时需用真实试做记录校准。",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def projections(items: list[dict], old: list[dict], old_verify: list[dict],
                db_rows: dict[str, dict], db_count: int,
                warnings: list[str]) -> dict[str, bytes]:
    legacy = legacy_applicability(items, old, old_verify)
    result = {
        "六套逐题蓝图.csv": csv_projection(items),
        "章节分值矩阵.csv": chapter_matrix(items),
        "考点覆盖矩阵.csv": coverage_matrix(items),
        "任务方式矩阵.csv": task_matrix(items),
        "修订对照.csv": revision_matrix(items, old),
        "旧复核适用性.json": json_bytes(legacy),
        "来源核对表.json": json_bytes(source_audit(items, db_rows, db_count, DB)),
        "规划核对结果.json": json_bytes(
            summary_report(items, db_rows, db_count, warnings, legacy)
        ),
    }
    for paper in range(1, 7):
        result["%02d_第%d套逐题设计.md" % (paper, paper)] = paper_md(
            items, paper, legacy
        )
    return result


def drift(produced: dict[str, bytes], directory: Path) -> list[str]:
    def normalize_crlf(content: bytes) -> bytes:
        return content.replace(b"\r\n", b"\n")

    changed = []
    for name, content in produced.items():
        path = directory / name
        if (not path.is_file()
                or normalize_crlf(path.read_bytes()) != normalize_crlf(content)):
            changed.append(name)
    return changed


def self_test() -> None:
    def require(condition: bool, description: str) -> None:
        if not condition:
            raise AssertionError(description)

    before = {"id": "S1-I01", "task": "求和", "data": "n=8",
              "answer_blueprint": "7"}
    after = dict(before, answer_blueprint="8")
    result = legacy_applicability(
        [after], [before], [{"items": ["S1-I01"], "name": "求和", "result": 7}]
    )
    require(result["核算项"][0]["状态"] == "旧结果失效待复核",
            "变更设计应使旧核算失效")
    require("评分骨架合计与题目分值不符" in rubric_errors({
        "points": 5, "rubric": [["求和式", 2], ["结果", 2]]
    }), "评分项算术错误应被拒绝")
    scratch_parent = ROOT / "_tmp"
    scratch_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch_parent) as temporary:
        root = Path(temporary)
        require(root.resolve().is_relative_to(ROOT.resolve()),
                "临时目录须落在项目内")
        (root / "proof.md").write_text("proof", encoding="utf-8")
        require(safe_reference(root, "proof.md"), "有效引用应可访问")
        require(not safe_reference(root, "../outside.md"),
                "越界引用应被拒绝")
        require(drift({"a.csv": b"first"}, root) == ["a.csv"],
                "缺少投影应被检测")
        (root / "a.csv").write_bytes(b"first")
        require(not drift({"a.csv": b"first"}, root),
                "相同投影不应报漂移")
        (root / "a.csv").write_bytes(b"stale")
        require(drift({"a.csv": b"first"}, root) == ["a.csv"],
                "过期投影应被检测")
        (root / "a.csv").write_bytes(b"first\r\nsecond\r\n")
        require(not drift({"a.csv": b"first\nsecond\n"}, root),
                "仅CRLF行尾转换不应报漂移")
        require(drift({"a.csv": b"first\nthird\n"}, root) == ["a.csv"],
                "CRLF文件中的正文变化应被检测")
        require(drift({"a.csv": b"first\rsecond\n"}, root) == ["a.csv"],
                "独立CR字符不能被当作普通行尾忽略")
    print("self-test: stale legacy check, rubric arithmetic, reference confinement, CRLF-aware projection drift OK")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="通过验证后覆盖生成的投影文件")
    parser.add_argument("--self-test", action="store_true",
                        help="运行与旧核验失效、评分、路径和投影漂移有关的自测")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    try:
        items = read_json(SOURCE)
        old = read_json(OLD_SOURCE)
        old_verify = read_json(OLD_VERIFY)
        db_rows, db_count = load_database(DB)
    except (OSError, json.JSONDecodeError, sqlite3.Error) as error:
        print("读取失败: " + str(error), file=sys.stderr)
        return 2
    errors, warnings = validate(items, db_rows, ROOT)
    for warning in warnings:
        print("WARN: " + warning, file=sys.stderr)
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        print("验证失败: " + str(len(errors)) + "项", file=sys.stderr)
        return 1
    expected = projections(items, old, old_verify, db_rows, db_count, warnings)
    if args.write:
        for name, content in expected.items():
            (PLAN / name).write_bytes(content)
        print("已生成" + str(len(expected)) + "个投影；主库只读。")
        return 0
    changed = drift(expected, PLAN)
    if changed:
        print("投影与唯一数据源不一致，请运行 --write：", file=sys.stderr)
        for name in changed:
            print("  " + name, file=sys.stderr)
        return 1
    print("蓝图与" + str(len(expected)) + "个投影一致；144题/900分。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
