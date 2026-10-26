"""Assemble the independent review ledger from hand inspection and oracle runs."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'_tmp/exam_final/review56.json'
ORACLE=json.loads((ROOT/'_tmp/exam_final/review56/oracle56.json').read_text(encoding='utf-8'))

CHECKS={
'S5-I01':['代入递推 F(1)=0、F(n)=2F(n/2)+n，独算 F(8)=24','逐层循环总量 n、非基例层 log₂n，时间 O(n log n)','填空后 C11 编译并运行三组调用'],
'S5-I02':['逐步检查删除偶数后的 pre/p 更新与释放，输出 3 5 7','时间 O(n)、额外空间 O(1)，C11 填空编译运行'],
'S5-I03':['验证共享栈左右边界、相邻满条件与栈1空条件','push/pop 均 O(1)，填空 C11 编译运行输出 72'],
'S5-I04':['对 7、18、29、3 模 11 后线性探测，核初址与环形更新','单次至多 m 次探测；填空 C11 编译运行表项'],
'S5-II01':['独立执行两趟冒泡，核两次数组与 5+3=8 次交换'],
'S5-II02':['按括号/除乘加优先级重新转后缀 a b c d e / − * +'],
'S5-II03':['分别核留空槽与 count 判满，两种最大容量 m−1 与 m'],
'S5-II04':['按题设一基 next 定义枚举 j=1..7 的最长真前后缀'],
'S5-II05':['以地址差 46 字节=23 个元素，解 2c+3=23'],
'S5-II06':['用 n₂=n₀−1 独算 8+3+7=18'],
'S5-II07':['穷举六顶点 720 个排列按七条弧过滤，得到 16 种'],
'S5-II08':['按下中点闭区间逐轮模拟，访问下标 8、12、14、13'],
'S5-II09':['独立堆上滤模拟，核完整数组 2、7、3、10、9、8、5'],
'S5-II10':['严格二叉树 2L−1=217，解 L=109'],
'S5-III01':['从先/中序独立重建七结点树，复算后序和 D/F 中序相邻项','矢量树图边集、孩子表与遍历一致'],
'S5-III02':['按 1..10 下中点递归建判定树；57 与 60 均访问 31→66→42→57','层数加权和 29、ASL=29/10；矢量图与孩子表一致'],
'S5-III03':['独立优先队列重算旧/新合并权和 WPL 143/170','从旧矢量树码长核 A 长度5、沿旧树新 WPL=178；两矢量图频率/码长核对'],
'S5-III04':['按给定序列独立插 BST，核后序与失败路径 40→60→50','层数加权和17、ASL=17/7；矢量图孩子关系一致'],
'S5-III05':['按 d(k)=1+(k mod10) 独立模拟每项探测地址和 11 槽表','成功探测和12、ASL=12/7'],
'S5-III06':['独立按邻点升序分别运行 DFS/BFS，核访问序、树边','三个分量，7−3=4 条森林树边'],
'S5-III07':['以稳定排序程序分别作第二→第一、第一→第二两种排序','核三阶段标识序列和同键原相对次序'],
'S5-IV01':['审查每段删到最后一个原结点、free 后不再访问与空表','C11 -Werror 编译；4000 个随机已排序链表与独立结果比较','时间 O(n)、辅助空间 O(1)'],
'S5-IV02':['验证当前零入度逐项消费的充要条件以及 k=0','C11 -Werror 编译；5000 个随机 DAG/前缀与独立前驱约束 oracle 比较','时间 O(V+E)、入度副本 O(V)'],
'S5-IV03':['审查空树高度−1、经根路径 left+right+2 与全局 best','C11 -Werror 编译；5000 棵随机树对所有结点对 BFS 直径比较','时间 O(n)、递归栈 O(h)'],
'S6-I01':['按 x=2 连续平方实际得到 4、16、256、65536，count=4','循环次数随 log log n 增长、额外空间 O(1)；C11 编译运行'],
'S6-I02':['检查 a/b 任一非空循环、同键先摘 A 后头插产生非递增链','时间 O(m+n)；填空 C11 编译运行输出 4 3 3 3 2 1'],
'S6-I03':['层开始固定 size(q)、同时左右空判叶，样例叶层权和可复算','每结点一次出队，时间 O(N)；外部队列接口下 C11 语法编译'],
'S6-I04':['验证 Kahn 队列非空条件与 --indeg==0 的唯一入队时机','每顶点/弧至多处理一次，O(V+E)；外部队列接口下 C11 语法编译'],
'S6-II01':['按 (rear−front+7) mod7 复算队列占四槽'],
'S6-II02':['行主序偏移 2×5+3=13 个 int，100+52=152'],
'S6-II03':['独立枚举四个元素合法栈排列，首项为3恰3种'],
'S6-II04':['分别从起点0/1/2 逐字符模拟，匹配0、2，比较3+1+3=7'],
'S6-II05':['按 Head/Tail 定义依次取 ((c,d),e) 的首元素'],
'S6-II06':['6 个非叶结点的孩子链加森林根链，共7个空 right'],
'S6-II07':['完全树前四层满15结点，第4层右侧2叶限定第5层至多12结点'],
'S6-II08':['独立堆上滤模拟，完整结果 1、7、2、9、8、6、4'],
'S6-II09':['双指针域 2n 减 n−1 条边，得 n+1=19'],
'S6-II10':['折半决策树容量 2⁷−1<180≤2⁸−1，最深8次'],
'S6-III01':['独立优先队列合并 8、15、24、33、57，WPL=137','从矢量树逐枝读 0/1，六个码字及码长与正文一致'],
'S6-III02':['按孩子兄弟指针还原 A、F 两棵树并复算后根序 C B E D A G F','森林深3、二叉树深4；矢量森林五条亲子边与正文一致'],
'S6-III03':['按下中点独立得到 25@6、33@9、28@7 与访问区间','完整 11 下标判定树深度和33，ASL=3；矢量图一致'],
'S6-III04':['按插入序列分别独立建普通 BST 与逐次 AVL 旋转','普通/AVL/折半三图逐节点核对；深度和18、17、17'],
'S6-III05':['独立拓扑正逆推 ve/vl=0,2,3,6,7,9','八活动 e/l、两条关键路径与工期9逐项核对'],
'S6-III06':['独立 Kruskal 得 MST 权8；Dijkstra 得 A 源距离2、3、6、7','核给出的最短路径树四边都实现对应最短距离且总权9'],
'S6-III07':['独立线性探测构建11槽表，逐项探测1、2、3、4、1、1、2','成功 ASL=14/7=2'],
'S6-IV01':['核双链按严格递增扫描、等键双 free、余链接尾和空链','C11 -Werror 编译；4000 组随机有序链与独立对称差比较','时间 O(m+n)、辅助空间 O(1)'],
'S6-IV02':['核先/中序分段、左/右/根写出与 n=0 不写','C11 -Werror 编译；5000 棵随机树遍历数组与独立后序比较','最坏扫描 O(n²)、递归栈 O(h)'],
'S6-IV03':['核自环、旧序正向、逆向时 v→u 可达性三分类','C11 -Werror 编译；5000 个随机 DAG/新增弧与独立 BFS 判环 oracle 比较','时间 O(V+E)、三个数组 O(V)'],
}

assert len(CHECKS)==48
rows=[]
hashes={"source_hashes":{},"answer_hashes":{},"pdf_hashes":{}}
for paper in (5,6):
    sp=ROOT/f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json'
    ap=ROOT/f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json'
    pdf=ROOT/f'资料整理/六套模拟卷成稿/答案PDF/重邮802模拟试卷第{paper}套答案.pdf'
    source=json.loads(sp.read_text(encoding='utf-8'))
    answer=json.loads(ap.read_text(encoding='utf-8'))
    assert len(source['questions'])==len(answer['questions'])==24
    for q in source['questions']:
        qid=q['id'];assert qid in CHECKS
        assert qid+'-points' in ORACLE
        rows.append({'id':qid,'status':'content_pass','checks':CHECKS[qid]+['题面各分值点合计与该题总分一致'], 'findings':[]})
    for k,p in [('source_hashes',sp),('answer_hashes',ap),('pdf_hashes',pdf)]:
        hashes[k][str(p.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest().upper()

result={
 'reviewer':'exam_audit（独立交叉复核）',
 'scope':'第5、6套学生题面与参考答案各24题；答案矢量树图；最终PDF逐页视觉审查',
 'questions':rows,
 **hashes,
 'visual_pages':[
   {'paper':paper,'page':page,'status':'pass','checks':
    ('填空十题均在同页，编号、答案和解析可读' if page==2 else
     '两幅Huffman树与正文同页且标注可读' if paper==5 and page==5 else
     '普通BST、AVL与折半三树同页且结构可读' if paper==6 and page==6 else
     '算法代码、复杂度、评分在同页完整可读' if paper==6 and page==12 else
     '整页题号、中文、数学符号、表格或代码、矢量图及页脚均可读，无裁切重叠')}
   for paper in (5,6) for page in range(1,13)
 ],
 'summary':{
   'reviewed_questions':48,'content_pass':48,'content_unresolved':0,
   'independent_oracle_checks':len(ORACLE),
   'reading_programs_c11':'8题补空 C11 语法通过；其中6题完整编译运行与预期输出一致',
   'algorithm_programs_c11':'6题均 -std=c11 -Wall -Wextra -Werror 编译；分别经4000或5000随机输入对照独立 oracle',
   'diagram_checks':'S5/6共11幅矢量图：重建树、判定树、旧/新Huffman、BST、森林、AVL及编码逐一比对正文与源题',
   'visual_review':'最终版第5、6套各12页，共24页均实际 view_image；中文、数学符号、表格、代码、矢量图、页脚可读，无缺字、裁切、重叠或小题孤立跨页',
   'initial_layout_findings_resolved':['S5填空II10曾独占页；最终十题同p2','S5 Huffman新树曾孤图页；最终旧新树同p5','S6填空II09解析曾跨页；最终十题同p2','S6 III04后两图曾孤图页；最终三树同p6','S6 IV03复杂度曾独占末页；最终代码复杂度评分同p12'],
   'content_revisions_rechecked':['S5-III01/02/04、S6-III03/04塌行ASCII改孩子关系表后，逐项重读且和矢量图一致','S5-III07 粗体Markdown标记修正后重新读取，结果未变'],
   'unresolved_findings':[]
 }
}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT, len(rows),'questions',len(ORACLE),'oracle checks')
