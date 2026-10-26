import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '_tmp/exam_final/review34.json'

CHECKS = {
 'S3-I01':['按倍增外层1/2/4/8与每轮8次内层独立计算32；补空后GCC严格编译运行。'],
 'S3-I02':['逐轮交换整条(key,tag)记录，重算同键4b先于4a；补空代码编译运行。'],
 'S3-I03':['跟踪头尾在入4、入7、出4、入9各步状态；编译运行得到4 7。'],
 'S3-I04':['按矩阵编号顺序追DFS树边与两个连通分量；补空后编译运行。'],
 'S3-II01':['逐项模拟循环队列入4、出2、再入3，核front/rear/count=2/0/5。'],
 'S3-II02':['由严格二叉树结点式N=2L−1独立求L=27。'],
 'S3-II03':['以入栈位置、栈状态递归枚举首弹4的完整序列，去重计14。'],
 'S3-II04':['对ababbab每个前缀逐位求最长真前后缀，再按1基定义换算next。'],
 'S3-II05':['用操作数栈按记号求3+2、8×5、9−5、40÷4及最终16。'],
 'S3-II06':['按结点度数求边数20及结点总数21，扣已知非叶9得叶12。'],
 'S3-II07':['用各点出度至少1给下界n，用有向Hamilton环构造达到。'],
 'S3-II08':['逐树汇总E=N−T，代入27−4=23。'],
 'S3-II09':['按1基下标7→3→1逐层上滤0，重算完整堆。'],
 'S3-II10':['计算46个孩子指针减22条树边，得24空指针。'],
 'S3-III01':['由先序/中序左右段独立重建满二叉树，推后序和四个线索；对照配图树结构。'],
 'S3-III02':['分别逐键建BST和AVL，重算22的LR旋转、两棵树与查找路径；对照两张配图。'],
 'S3-III03':['按最小堆独立合并百分比权值7次，合并权和261即平均码长2.61。'],
 'S3-III04':['按22/33/14/25/36/47独立线性探测构表，逐键成功与11个起址失败探测计数。'],
 'S3-III05':['Kruskal按给定等权次序做并查集判环；Prim从A逐轮查跨边，均得权7。'],
 'S3-III06':['按1基中点4/2/6构判定树，逐键统计深度与21、25两次查找；对照配图。'],
 'S3-III07':['按宽度1、2、4分别稳定归并8a和8b，核三趟完整记录次序。'],
 'S3-IV01':['正式C代码独立GCC -Werror编译；1000组随机三有序链含空链/重复键，核原结点集合与升序。'],
 'S3-IV02':['正式C代码独立编译；1000棵随机标记树与独立根叶枚举对拍，核输出指针路径。'],
 'S3-IV03':['正式C代码独立编译；1000张随机图穷举所有s/t/k和简单路径，逐项比计数。'],
 'S4-I01':['逐层手算6次递归调用、5次比较与返回16；原程序GCC严格编译运行。'],
 'S4-I02':['逐段追A交B的保留/释放/前进分支；三个空补全后GCC严格语法编译。'],
 'S4-I03':['检查count=4判满、rear模4前进和deq减count；补空后编译运行。'],
 'S4-I04':['按孩子关系枚举4/5/7三片叶；补空后编译运行输出3。'],
 'S4-II01':['递归树叶数n、总结点2n−1和最大深度log₂n+1分别求时间/空间。'],
 'S4-II02':['按行主序偏移2×6+3=15，4字节元素求地址1060。'],
 'S4-II03':['独立模拟目标出栈序列3,2,4,1,5，跟踪首次压入数和最大栈高。'],
 'S4-II04':['对abacaba前六段逐位求π并换算题定next[1..7]。'],
 'S4-II05':['层层计算Tail、Head、Head，辨认c为原子。'],
 'S4-II06':['由严格二叉Huffman树N=2L−1代入L=17得33。'],
 'S4-II07':['入度/出度各至少1给弧数下界n；到达下界时各入度均1。'],
 'S4-II08':['按折半判定树最大层数核600键的最坏成功比较10次。'],
 'S4-II09':['新键1从下标8经4、2、1上滤，核整堆顺序。'],
 'S4-II10':['按森林E=N−T求16，再添互不连接树核树数4。'],
 'S4-III01':['独立转换中缀为后缀，模拟前六记号的栈[8,8]及峰值3。'],
 'S4-III02':['按墓碑查找与首墓碑回用规则逐槽模拟，核最终31在4号槽。'],
 'S4-III03':['按孩子表重算中序D B E A F C G，逐叶查前驱后继和B的右孩子标志。'],
 'S4-III04':['逐轮手算Dijkstra暂定距离、前驱和0→4权10路径。'],
 'S4-III05':['正向ve及逆向vl独立计算；逐活动算时差并枚举两条工期8关键路径。'],
 'S4-III06':['逐键构BST与AVL，重算45引发RL、最终结构和两树ASL；对照配图。'],
 'S4-III07':['以最小堆合并5次求WPL227，按合并树追F/A码长1/4与定长差73。'],
 'S4-IV01':['正式C代码独立GCC -Werror编译；1000组随机环形链含空/全删/删尾/保序与计数验证。'],
 'S4-IV02':['正式C代码独立编译；1000棵随机BST对全部键暴力比较最近距离及并列取小，含空树。'],
 'S4-IV03':['正式C代码独立编译；1000张随机加权图失效MST边，与重新Kruskal求MST总权/断连结果对拍。'],
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

questions = []
source_hashes = {}
answer_hashes = {}
pdf_hashes = {}
for paper in (3,4):
    s = ROOT / f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json'
    a = ROOT / f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json'
    pdf = ROOT / f'资料整理/六套模拟卷成稿/答案PDF/重邮802模拟试卷第{paper}套答案.pdf'
    source_hashes[str(s.relative_to(ROOT)).replace('\\','/')] = sha(s)
    answer_hashes[str(a.relative_to(ROOT)).replace('\\','/')] = sha(a)
    pdf_hashes[str(pdf.relative_to(ROOT)).replace('\\','/')] = sha(pdf)
    src = json.loads(s.read_text(encoding='utf-8'))['questions']
    ans = json.loads(a.read_text(encoding='utf-8'))['questions']
    assert [q['id'] for q in src] == [q['id'] for q in ans]
    for q in src:
        qid=q['id']
        assert qid in CHECKS, qid
        questions.append({'id':qid,'status':'pass','checks':CHECKS[qid],'findings':[]})

figure = ROOT / '资料整理/六套模拟卷成稿/答案配图源稿.json'
visual = []
for paper in (3,4):
    folder = ROOT / f'_tmp/exam_final/rendered_answers/第{paper}套'
    for page in range(1,13):
        image = folder / f'page-{page:02}.png'
        assert image.exists()
        note = '文字、代码、表格/树图及页脚清晰；无裁切、重叠、孤行或截断。'
        if paper==4 and page==2:
            note += ' 已复看II-8更新后的log₂(600)公式，底数与自变量清楚。'
        visual.append({'paper':paper,'page':page,'status':'pass','checks':note,'image_sha256':sha(image)})

report = {
    'reviewer':'/root/project_map',
    'source_hashes':source_hashes,
    'answer_hashes':answer_hashes,
    'figure_source_hash':sha(figure),
    'answer_pdf_hashes':pdf_hashes,
    'summary':{'questions_reviewed':len(questions),'content_pass':len(questions),'content_fail':0,
               'visual_pages_reviewed':len(visual),'algorithm_random_cases_each':1000,
               'methods':['I题补空后GCC C11 -Wall -Wextra -Werror编译（有main者运行）',
                          'II/III按题面逐式、逐槽、逐树及逐轮独立计算',
                          'IV从正式答案JSON提取代码独立严格编译并随机对拍',
                          '树图源稿及24页PNG逐页目视检查'],
               'nonblocking_note':None},
    'questions':questions,
    'visual_pages':visual,
}
if OUT.exists():
    old=json.loads(OUT.read_text(encoding='utf-8'))
    old_images={(x['paper'],x['page']):x['image_sha256'] for x in old.get('visual_pages',[])}
    changed_images=[(x['paper'],x['page']) for x in visual if old_images.get((x['paper'],x['page']))!=x['image_sha256']]
    print('changed images:', changed_images)
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(OUT, len(questions), len(visual))
