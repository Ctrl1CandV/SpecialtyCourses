"""Write the independently performed review in a machine-readable form."""

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "_tmp/exam_final/review12.json"

CHECKS = {
    "S1-I01": "逐层展开 span=1,2,4,8，核 15 次执行、outSum=47 与 O(n)",
    "S1-I02": "逐指针复原前驱插入后的链关系和两次打印结果",
    "S1-I03": "逐步追踪循环单链队列入队、单结点出队与 rear 状态",
    "S1-I04": "空树、叶结点、非叶结点递归归纳，并核示例三次输出",
    "S1-II01": "按栈规则独立重建中缀对应后缀式",
    "S1-II02": "行优先地址偏移 14×4=56 独立计算",
    "S1-II03": "按留空槽循环队列定义重算长度与满条件",
    "S1-II04": "按题给 π 与 next 定义直接逐前后缀检查",
    "S1-II05": "按广义表 Tail 后取 Head 的层级独立展开",
    "S1-II06": "按前5层31结点及第5层4叶构造最大结点数55",
    "S1-II07": "穷举全部42个合法出栈序列，首个为3的有9个",
    "S1-II08": "按 AVL 插入和旋转复原满平衡7结点树",
    "S1-II09": "上滤 85 的两次父子位置判断，核左孩子70",
    "S1-II10": "折半查找最深成功结点及容量界限复核",
    "S1-III01": "先中序分割重建，再独立核后序及 C/G 线索；配图孩子关系一致",
    "S1-III02": "最小堆重建合并序、码字和 WPL=91；配图码边一致",
    "S1-III03": "独立线性探测脚本核全表、成功探测与11起点失败探测",
    "S1-III04": "按下取整 mid 递归建判定树，重算 ASL=29/10 和27轨迹；配图一致",
    "S1-III05": "独立按 Prim 割边与 Kruskal 并查集核入树顺序和权和16",
    "S1-III06": "逐次 BST/AVL 插入复原 LR、RL 与最终树；两张配图一致",
    "S1-III07": "用题给挖坑代码和独立下滤器逐步模拟两数组",
    "S1-IV01": "独立 GCC C11 严格编译；300组有序链表随机差集与 B 不变 oracle",
    "S1-IV02": "独立 GCC C11 严格编译；400棵随机含负权树核最优和、合法根叶路径及长度",
    "S1-IV03": "独立 GCC C11 严格编译；400张随机无向图用禁点 BFS 对照路径存在性和简单路径契约",
    "S2-I01": "由 M(n)=2M(n-1)+1 展开 n=3 移动7次，核 O(2^n)",
    "S2-I02": "逐指针复原双向相邻结点交换和示例前后打印",
    "S2-I03": "核两栈相邻满条件、右栈先减后写和先取后增",
    "S2-I04": "空/单叶/链状树检查高度哨兵和示例输出",
    "S2-II01": "按先弹右操作数规则独立算后缀表达式14",
    "S2-II02": "穷举4元素合法出栈序列共14个",
    "S2-II03": "按题给 front/rear 约定重算队长3与 rear=2",
    "S2-II04": "逐前后缀核 aaaaab 的 next[6]=5 与 π(6)=0",
    "S2-II05": "行优先三维数组偏移17元素、68字节重算",
    "S2-II06": "以森林边数=结点数-根数核3棵",
    "S2-II07": "用2n指针与n-1孩子边核 n+1 空指针",
    "S2-II08": "下取整中点建16结点判定树，核最大成功比较5次",
    "S2-II09": "逐层上滤12核最终下标3及比较2次",
    "S2-II10": "严格二叉树 L=I+1 与 L+I=15 核叶数8",
    "S2-III01": "按孩子兄弟规则独立生成孩子表、先后根、边数；配图一致",
    "S2-III02": "递归折半建树并穷举9个失败间隙深度；配图一致",
    "S2-III03": "独立哈希 oracle 核两法全表、成功/失败 ASL 与拉链比较定义",
    "S2-III04": "独立最短路重算 Dijkstra 轮次、最终距离及 A→E 路径",
    "S2-III05": "独立拓扑正反递推 ve/vl，核唯一关键路径和工期8",
    "S2-III06": "最小堆独立重建 Huffman 合并、码字和 WPL=86；配图一致",
    "S2-III07": "独立插入排序状态及挖坑划分脚本核四小问",
    "S2-IV01": "独立 GCC C11 严格编译；400组随机正负链核稳定分组与边界",
    "S2-IV02": "独立 GCC C11 严格编译；400棵随机树核逐结点叶数及空树",
    "S2-IV03": "独立 GCC C11 严格编译；500张随机图用 BFS 距离 oracle 核 k<0/s=t/路径限长",
}

RESOLVED = {
    "S1-II01": "旧版 PDF 曾印出字面 **；作者已改为普通标签，最终第2页复看通过。",
    "S1-IV02": "独立复核提出 int 返回值范围歧义；题面已明确路径和在 int 范围内，当前契约通过。",
    "S2-IV01": "旧版答案缺 NULL 所需标准头；作者已补 <stddef.h>，当前独立编译通过。",
    "S2-IV02": "旧版答案缺 NULL 所需标准头；作者已补 <stddef.h>，当前独立编译通过。",
    "S2-IV03": "旧版答案缺 NULL 所需标准头；作者已补 <stddef.h>，当前独立编译通过。",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    all_questions = []
    source_hashes, answer_hashes, pdf_hashes = {}, {}, {}
    for paper in (1, 2):
        src = ROOT / f"资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json"
        ans = ROOT / f"资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json"
        pdf = ROOT / f"资料整理/六套模拟卷成稿/答案PDF/重邮802模拟试卷第{paper}套答案.pdf"
        source_hashes[str(paper)] = sha(src)
        answer_hashes[str(paper)] = sha(ans)
        pdf_hashes[str(paper)] = sha(pdf)
        source = json.loads(src.read_text(encoding="utf-8"))["questions"]
        answers = json.loads(ans.read_text(encoding="utf-8"))["questions"]
        a_by_id = {x["id"]: x for x in answers}
        assert len(source) == len(answers) == 24
        assert {x["id"] for x in source} == set(a_by_id)
        assert collections.Counter((x["section"], x["points"]) for x in source) == {
            ("I", 5): 4, ("II", 3): 10, ("III", 10): 7,
            ("IV", 8): 1, ("IV", 10): 1, ("IV", 12): 1,
        }
        assert sum(x["points"] for x in source) == 150
        for q in source:
            id = q["id"]
            assert id in CHECKS and a_by_id[id]["content"]
            for ref in a_by_id[id].get("references", []):
                assert (ROOT / ref["path"]).exists(), (id, ref)
            all_questions.append({
                "id": id,
                "status": "pass",
                "checks": [CHECKS[id], "题面与答案逐项对照，分值和小问完整"],
                "findings": [RESOLVED[id]] if id in RESOLVED else [],
            })
    assert len(all_questions) == len(CHECKS) == 48
    visual = []
    for paper in (1, 2):
        for page in range(1, 13):
            png = ROOT / f"_tmp/exam_final/rendered_answers/第{paper}套/page-{page:02}.png"
            assert png.exists()
            visual.append({
                "paper": paper,
                "page": page,
                "status": "pass",
                "checks": "实际以原分辨率逐页查看文字、分数、代码、表格、配图、页脚和裁切；最终重渲染版复看",
                "findings": [],
            })
    report = {
        "reviewer": "repo_quality（独立交叉复核）",
        "source_hashes": source_hashes,
        "answer_hashes": answer_hashes,
        "answer_pdf_hashes": pdf_hashes,
        "questions": all_questions,
        "visual_pages": visual,
        "summary": {
            "question_count": 48,
            "passed_questions": 48,
            "visual_pages_reviewed": 24,
            "unresolved_findings": 0,
            "resolved_findings": list(RESOLVED),
            "independent_checks": [
                "verify_numeric.py：栈序列、折半、散列、Huffman、排序过程、Dijkstra、AOE 均通过",
                "verify_iv.py：六道算法答案源码 GCC C11 -Wall -Wextra -Werror 独立编译通过",
                "verify_iv.py：共2400组随机/边界 oracle 对照通过",
                "答案配图源稿.json：7题8幅树图/码字图与答案文字逐一核对",
                "两套均为24题150分；48题所列参考路径均存在",
            ],
            "limitations": "随机测试与示例覆盖不能替代对全部可能输入的形式证明；本次已结合代码不变量和边界人工审查。",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
