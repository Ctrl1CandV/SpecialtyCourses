import json
from pathlib import Path
from p1 import ANSWERS as P1
from p2 import ANSWERS as P2

ROOT = Path(__file__).resolve().parents[3]
BLUEPRINT = json.loads((ROOT / '资料整理/六套模拟卷规划/六套逐题蓝图.json').read_text(encoding='utf-8'))
META = {q['id']: q for q in BLUEPRINT}

ANSWER_PAGES = {
    2024: {'I': '物理第14—15页，2024程序阅读答案',
           'II': '物理第16—18页，2024填空答案',
           'III': '物理第19—23页，2024综合应用答案',
           'IV': '物理第23—25页，2024算法题答案'},
    2025: {'I': '物理第28—30页，2025程序阅读答案',
           'II': '物理第31—33页，2025填空答案',
           'III': '物理第33—38页，2025综合应用答案',
           'IV': '物理第39—42页，2025算法题答案'},
    2026: {'I': '物理第1—4页，2026程序阅读答案',
           'II': '物理第4—6页，2026填空答案',
           'III': '物理第7—10页，2026综合应用答案',
           'IV': '物理第10—12页，2026算法题答案'},
}


def references(qid):
    row = META[qid]
    evidence = row.get('pdf_evidence') or []
    assert evidence, qid
    result = []
    for ev in evidence:
        path = ev['path']
        assert (ROOT / path).exists(), (qid, path)
        result.append({
            'path': path,
            'location': f"物理第{ev['pdf_page']}页，{ev['year']}年{ev['question']}",
            'use': '参考本校试题的知识点及设问形式；本题数据与结论独立复核',
        })
    year = evidence[0]['year']
    answer_path = ('真题资料/真题24-25.pdf' if year in (2024, 2025)
                   else '真题资料/重邮2026年802真题答案.pdf')
    result.append({
        'path': answer_path,
        'location': ANSWER_PAGES[year][row['section']],
        'use': '参考历年答案的推导与作答格式；本题答案由题面独立计算和验证',
    })
    return result


for paper, answers in ((1, P1), (2, P2)):
    exam_path = ROOT / f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json'
    exam = json.loads(exam_path.read_text(encoding='utf-8'))
    ids = [q['id'] for q in exam['questions']]
    assert len(ids) == len(set(ids)) == 24
    assert set(ids) == set(answers), (paper, set(ids) - set(answers), set(answers) - set(ids))
    questions = []
    for qid in ids:
        content, checks = answers[qid]
        assert content and checks
        assert 'Θ(' not in content
        questions.append({'id': qid, 'content': content,
                          'references': references(qid), 'checks': checks})
    out = {'paper': paper, 'version': '2026-10-25-answer-v1', 'questions': questions}
    out_path = ROOT / f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(out_path, 'questions=', len(questions))
