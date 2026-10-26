"""Create WPS-friendly click-through process diagrams for C2-B lessons.

The changing picture is exported as separate transparent PNG states; one click
replaces the previous state. Exam code stays as editable text on its code page.
"""
from pathlib import Path
import html
import yaml

ROOT = Path(__file__).resolve().parents[2] / '课程' / '课件' / 'C2' / 'C2-B-pro'
BOX = [0.9, 2.58, 11.55, 3.78]


def esc(value):
    return html.escape(str(value), quote=True)


def pill(value, state="plain", label=None):
    colors = {
        "plain": ("#FFFFFF", "#B9C3D0", "#1F2329"),
        "active": ("#E8EEF9", "#1F4E9C", "#173B77"),
        "done": ("#E8F4EE", "#4B8B68", "#28583D"),
        "removed": ("#FDEDEC", "#D46A63", "#8F3734"),
        "hole": ("#F5F6F8", "#9AA3AE", "#68707C"),
    }
    bg, border, fg = colors[state]
    content = f'<div style="min-width:62px;height:54px;padding:0 12px;border:2px solid {border};border-radius:12px;background:{bg};color:{fg};display:flex;align-items:center;justify-content:center;font-size:31px;font-weight:700;box-sizing:border-box">{esc(value)}</div>'
    if label:
        content = f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px"><span style="font-size:21px;color:#1F4E9C;font-weight:700">{esc(label)}</span>{content}</div>'
    return content


def row(values, active=(), done=(), removed=(), labels=None):
    active, done, removed = set(active), set(done), set(removed)
    labels = labels or {}
    out = []
    for i, value in enumerate(values):
        state = "active" if i in active else "done" if i in done else "removed" if i in removed else "plain"
        out.append(pill(value, state, labels.get(i)))
    return '<div style="display:flex;align-items:center;justify-content:center;gap:13px;flex-wrap:wrap">' + "".join(out) + "</div>"


def panel(title, body, detail=""):
    extra = f'<div style="font-size:25px;line-height:1.3;color:#515B68;margin-top:14px">{detail}</div>' if detail else ""
    return f'<section style="background:#FFFFFF;border:1px solid #D8DEE8;border-radius:16px;padding:20px 22px;display:flex;flex-direction:column;justify-content:center;min-height:150px;box-sizing:border-box"><div style="font-size:27px;color:#1F4E9C;font-weight:700;margin-bottom:15px">{title}</div>{body}{extra}</section>'


def svg_tree(coords, edges, labels, active=(), done=(), removed=(), width=850, height=340):
    active, done, removed = set(active), set(done), set(removed)
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">']
    for a, b in edges:
        if not labels[a] or not labels[b]:
            continue
        x1, y1 = coords[a]; x2, y2 = coords[b]
        parts.append(f'<line x1="{x1}" y1="{y1+27}" x2="{x2}" y2="{y2-27}" stroke="#7E8996" stroke-width="4"/>')
    for i, label in enumerate(labels):
        if not label:
            continue
        x, y = coords[i]
        if i in active: fill, stroke, color = "#E8EEF9", "#1F4E9C", "#173B77"
        elif i in done: fill, stroke, color = "#E8F4EE", "#4B8B68", "#28583D"
        elif i in removed: fill, stroke, color = "#FDEDEC", "#D46A63", "#8F3734"
        else: fill, stroke, color = "#FFFFFF", "#7E8996", "#1F2329"
        parts.append(f'<circle cx="{x}" cy="{y}" r="27" fill="{fill}" stroke="{stroke}" stroke-width="4"/><text x="{x}" y="{y+10}" text-anchor="middle" font-family="Arial,Microsoft YaHei,sans-serif" font-size="28" font-weight="700" fill="{color}">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_graph(coords, edges, labels, active=(), done=(), failed=(), directed=False, width=850, height=350):
    active, done, failed = set(active), set(done), set(failed)
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">']
    if directed:
        parts.append('<defs><marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#7E8996"/></marker></defs>')
    for edge in edges:
        a, b = edge[:2]; x1, y1 = coords[a]; x2, y2 = coords[b]
        if directed:
            dx, dy = x2 - x1, y2 - y1
            length = (dx * dx + dy * dy) ** 0.5
            ux, uy = dx / length, dy / length
            # Stop at the node border so the arrow head remains visible.
            x1, y1 = x1 + ux * 29, y1 + uy * 29
            x2, y2 = x2 - ux * 34, y2 - uy * 34
            parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#7E8996" stroke-width="4" marker-end="url(#arr)"/>')
        else:
            parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#7E8996" stroke-width="4"/>')
    for i, label in enumerate(labels):
        x, y = coords[i]
        if i in active: fill, stroke, color = "#E8EEF9", "#1F4E9C", "#173B77"
        elif i in done: fill, stroke, color = "#E8F4EE", "#4B8B68", "#28583D"
        elif i in failed: fill, stroke, color = "#FDEDEC", "#D46A63", "#8F3734"
        else: fill, stroke, color = "#FFFFFF", "#7E8996", "#1F2329"
        parts.append(f'<circle cx="{x}" cy="{y}" r="28" fill="{fill}" stroke="{stroke}" stroke-width="4"/><text x="{x}" y="{y+10}" text-anchor="middle" font-family="Arial,Microsoft YaHei,sans-serif" font-size="27" font-weight="700" fill="{color}">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def frame(title, subtitle, panels, footer):
    columns = min(max(len(panels), 1), 3)
    grid = f'<div style="display:grid;grid-template-columns:repeat({columns},1fr);gap:16px;flex:1;min-height:0">' + "".join(panels) + "</div>"
    return f'''<div style="width:100%;height:100%;box-sizing:border-box;padding:23px 27px;background:#F7F9FC;border:1px solid #D8DEE8;border-radius:16px;display:flex;flex-direction:column;gap:12px;overflow:hidden;font-family:Arial,'Microsoft YaHei',sans-serif;color:#1F2329">
<div style="font-size:37px;line-height:1.12;font-weight:700;color:#1F4E9C">{title}</div>
<div style="font-size:24px;line-height:1.25;color:#515B68">{subtitle}</div>
{grid}
<div style="padding:12px 16px;background:#E8EEF9;border-radius:10px;font-size:25px;line-height:1.2;font-weight:600;color:#243B5A">{footer}</div></div>'''


def chain_panel(title, values, detail, active=(), done=(), removed=(), labels=None):
    return panel(title, row(values, active, done, removed, labels), detail)


def write_page(lesson, page, frames):
    directory = ROOT / f"C2-B-{lesson:02d}" / "pages"
    directory.mkdir(parents=True, exist_ok=True)
    anim = []
    for i, html_text in enumerate(frames):
        anim.append({"id": "initial" if i == 0 else f"s{i}", "component": "raw", "box": BOX, "props": {"html": html_text}})
    steps = []
    for i in range(1, len(frames)):
        steps.append({"hide": ["initial" if i == 1 else f"s{i-1}"], "appear": [f"s{i}"]})
    spec = {"page": page, "anim": anim, "steps": steps}
    (directory / f"p{page:02d}.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=130), encoding="utf-8")


def build():
    # B02 P5 — merge two increasing lists by taking the smaller node to the head.
    frames = []
    states = [
        (([1,3,5],[2,4,6],[]), "pa=1，pb=2；结果表为空"),
        (([3,5],[2,4,6],[1]), "1<2，摘下1头插；pa前进到3"),
        (([3,5],[4,6],[2,1]), "3>2，摘下2头插；pb前进到4"),
        (([5],[4,6],[3,2,1]), "3<4，摘下3；结果变成3→2→1"),
        (([5],[6],[4,3,2,1]), "5>4，摘下4；较小者仍是先处理对象"),
        (([],[6],[5,4,3,2,1]), "5<6，摘下5；A 已空，进入收尾循环"),
        (([],[],[6,5,4,3,2,1]), "收尾头插6；两条输入链耗尽，归并结束"),
    ]
    for i, (data, status) in enumerate(states):
        a,b,out=data
        frames.append(frame("归并成递减链：每次摘较小结点并头插", "输入链仍递增；输出链头插后自然递减", [
            chain_panel("A · pa", a or ["空"], "按递增顺序读取", active=[0] if a else []),
            chain_panel("B · pb", b or ["空"], "与 pa 当前结点比较", active=[0] if b else []),
            chain_panel("结果 · la", out or ["空"], "新结点接到表头")], status))
    write_page(2,5,frames)

    # B02 P8 — split, reverse the suffix, then weave.
    states = [
        ("找中点", "slow 最终停在 a3；a3 是前半段最后一个结点。", ["a1","a2","a3","a4","a5","a6"], [2], []),
        ("断开两段", "在 a3 后断链；前半和后半先分开。", ["a1","a2","a3"], [], []),
        ("逆置后半", "a4→a5→a6 头插成 a6→a5→a4。", ["a6","a5","a4"], [], []),
        ("交替插入一轮", "a6 插到 a1 后；first 前进到 a2，second 前进到 a5。", ["a1","a6","a2","a3"], [1], []),
        ("完成", "继续插入 a5、a4，最终为 a1→a6→a2→a5→a3→a4。", ["a1","a6","a2","a5","a3","a4"], [], []),
    ]
    frames=[]
    for title,detail,vals,active,done in states:
        panels=[chain_panel("当前链 / 操作结果", vals, detail, active=active, done=done),
                panel("处理顺序", '<div style="font-size:31px;line-height:1.55">① 快慢指针找中点<br>② 断开并逆置后半<br>③ 两段交替接回</div>', "p、q 更新前先保存各自后继")]
        frames.append(frame("链表重排：找中点、逆置、再交替", title, panels, detail))
    write_page(2,8,frames)

    # B02 P10 — Josephus, starting at s=1 and counting m=3.
    states=[
        ([1,2,3,4,5],[],"从1开始报数：1、2、3；删除3，从4接着数。"),
        ([1,2,4,5],[3],"删除3；pre停在2，新的p指向4。"),
        ([2,4,5],[3,1],"从4数4、5、1，删除1；下一轮从2开始。"),
        ([2,4],[3,1,5],"从2数2、4、5，删除5；2与4继续成环。"),
        ([4],[3,1,5,2],"删除2后只剩4；返回4，循环结束。"),
    ]
    frames=[]
    for values, removed, detail in states:
        panels=[chain_panel("仍在环中的结点（末尾接回开头）", values, "p 指向本轮起点；pre 指向它的前驱", active=[0]),
                chain_panel("已出列顺序", removed or ["—"], detail, done=range(len(removed)))]
        frames.append(frame("约瑟夫环：n=5，s=1，m=3", "每次报到第3个结点就摘除，再从后继继续", panels, detail))
    write_page(2,10,frames)

    # B03 P7 — infix conversion and a compact evaluation trace.
    states=[
        ("开始", "当前读到3", "", "", ""),
        ("输出操作数", "读到3，直接输出", "", "3", ""),
        ("左括号入栈", "读到(，压入运算符栈", "(", "3", ""),
        ("运算符入栈", "读到+；括号内没有更高或同级运算符", "(  +", "3", ""),
        ("继续输出", "读到4，追加到后缀串", "(  +", "3  4", ""),
        ("遇右括号", "弹出+并丢弃匹配的(；括号外*随后入栈", "*", "3  4  +", ""),
        ("读完表达式", "输出2；扫描结束后弹出*", "", "3  4  +  2  *", ""),
        ("后缀求值", "3、4入栈，+得7；再压2，*得14。", "", "3  4  +  2  *", "[14]"),
    ]
    frames=[]
    for title,detail,ops,out,values in states:
        panels=[panel("运算符栈（底 → 顶）", row(ops.split() or ["空"], active=[len(ops.split())-1] if ops else []), "遇到右括号时弹到左括号"),
                panel("后缀输出 / 求值栈", f'<div style="font-size:34px;line-height:1.5;font-weight:700;color:#28583D">{out or "—"}</div><div style="margin-top:15px;font-size:29px;color:#1F4E9C">求值栈：{values or "等待后缀式"}</div>', "操作数次序：先弹出的是右操作数")]
        frames.append(frame("表达式 (3+4)*2：转后缀 34+2*，再求值", title, panels, detail))
    write_page(3,7,frames)

    # B04 P5 — recursive height expansion and return.
    coords={0:(425,54),1:(240,145),2:(610,145),3:(140,255),4:(340,255),5:(520,255),6:(700,255)}
    edges=[(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]; labels=["1","2","3","4","5","6","7"]
    states=[
        ("调用根结点1", "TreeDepth(1) 先递归左子树，再递归右子树。", [0], []),
        ("展开左子树", "1→2；2再调用4和5，空孩子返回0。", [1,3,4], []),
        ("左子树返回高度2", "h(4)=h(5)=1，所以 h(2)=max(1,1)+1=2。", [], [1,3,4]),
        ("右子树返回高度2", "h(6)=h(7)=1，所以 h(3)=2。", [], [2,5,6]),
        ("回到根结点", "h(1)=max(2,2)+1=3；整棵树高度为3。", [0], [1,2,3,4,5,6]),
    ]
    frames=[]
    for title,detail,active,done in states:
        svg=svg_tree(coords,edges,labels,active,done)
        panels=[panel("递归树",svg),panel("返回值", '<div style="font-size:32px;line-height:1.55">空树 → 0<br>叶子 → 1<br>结点 → max(左,右)+1</div>', detail)]
        frames.append(frame("求高度：沿调用向下，再把结果逐层带回", title, panels, detail))
    write_page(4,5,frames)

    # B05 P4 — level width and the last/rear boundary.
    coords={0:(425,55),1:(250,155),2:(600,155),3:(150,260),4:(340,260),5:(570,260)}
    edges=[(0,1),(0,2),(1,3),(1,4),(2,5)]; labels=["1","2","3","4","5","6"]
    states=[
        ("准备开始", [], [], "队列只有根1；last标记本层最后一个结点。", ["1"], "2、3 待处理"),
        ("第1层结束", [0], [], "出队1，2和3入队；front越过last=1，宽度记1，last改指3。", ["1"], "2  3"),
        ("第2层结束", [1,2], [], "出队2、3，再把4、5、6入队；宽度记2，last改指6。", ["2","3"], "4  5  6"),
        ("第3层结束", [3,4,5], [], "4、5、6出队后无新孩子；最大宽度更新为3。", ["4","5","6"], "空"),
    ]
    frames=[]
    for title,active,done,detail,queue,waiting in states:
        svg=svg_tree(coords,edges,labels,active,done)
        panels=[panel("按层扫描的二叉树",svg),panel("队列与边界", f'<div style="font-size:28px;line-height:1.55">当前层队列：{esc("，".join(queue))}<br>下一层：{esc(waiting)}<br>front 越过 last：本层完成</div>', detail)]
        frames.append(frame("树的宽度：front、rear、last 怎样对齐", title, panels, detail))
    write_page(5,4,frames)

    # B05 P8 — current path versus the saved longest path.
    coords={0:(425,45),1:(240,130),2:(610,130),3:(145,220),4:(330,220),5:(330,305)}
    edges=[(0,1),(0,2),(1,3),(1,4),(3,5)]; labels=["1","2","3","4","5","6"]
    states=[
        ("初始状态", [0], [], [0], "path=[1]，pathLen=1；maxPath尚未更新。"),
        ("进入左子树", [0,1], [], [0,1], "path=[1,2]，pathLen=2；递归接着走到4，再走到6。"),
        ("到达叶子6", [0,1,3,5], [], [0,1,3,5], "path=[1,2,4,6]，pathLen=4；超过maxLen，复制到maxPath。"),
        ("回退后试结点5", [0,1,4], [0,1,3,5], [0,1,4], "pathLen按值传递，退回结点4时仍是3；结点5形成长度3的路径。"),
        ("回到根后试右侧", [0,2], [0,1,3,5], [0,1,3,5], "路径1→3较短；最长结果保持1→2→4→6，长度4。"),
    ]
    frames=[]
    for title,active,done,pathnodes,detail in states:
        svg=svg_tree(coords,edges,labels,active,done)
        current=" → ".join(labels[i] for i in pathnodes)
        panels=[panel("递归访问",svg),panel("数组状态", f'<div style="font-size:29px;line-height:1.6">path：{current}<br>pathLen：{len(pathnodes)}<br>maxPath：1 → 2 → 4 → 6<br>maxLen：4</div>', detail)]
        frames.append(frame("最长根到叶路径：path 随调用变化，maxPath 单独保存", title, panels, detail))
    write_page(5,8,frames)

    # B06 P7 — explain why the two independent reachability searches reset visited.
    coords={0:(130,165),1:(300,80),2:(300,250),3:(490,165),4:(650,80),5:(760,80)}
    edges=[(0,1),(0,2),(1,3),(2,3),(1,4),(4,5)]; labels=["0","1","2","3","4","5"]
    states=[
        ("准备搜索", "目标是先从0到3，再从3到5；两次搜索共享visited会留下标记。", [], [], []),
        ("先搜 u=0 到 k=3", "沿0→1→3到达k；本轮把0、1、3标记为已访问。", [0,1,3], [], []),
        ("不清零就从3再搜5", "3的邻点1已标记；绕到2后又被0挡住，错误地返回false。", [2], [], [0,1,3]),
        ("两段之间清零", "重新从3搜索，可到1→4→5；本例按两段独立可达的题意返回true。", [3,1,4,5], [0,3,1,4,5], []),
    ]
    frames=[]
    for title,detail,active,done,failed in states:
        svg=svg_graph(coords,edges,labels,active,done,failed)
        panels=[panel("无向图：u=0，k=3，v=5",svg),panel("visited 状态", f'<div style="font-size:29px;line-height:1.55">第一段：0 能到 3<br>第二段：3 能到 5<br>两段之间是否清零？</div>', detail)]
        frames.append(frame("visited 的复位：两次可达搜索不能共享旧标记", title, panels, detail))
    write_page(6,7,frames)

    # B06 P9 — Kahn topological sort with a stack.
    coords={0:(110,90),1:(285,90),2:(285,260),3:(515,175),4:(730,175)}
    edges=[(0,1),(0,2),(1,3),(2,3),(3,4)]; labels=["0","1","2","3","4"]
    states=[
        ("初始化", [], [], "入度=[0,1,1,2,1]；只有0入栈。", [], ["0"]),
        ("弹出0", [0], [], "输出0；1和2入度归零，按扫描顺序入栈，栈顶是2。", ["0"], ["1","2"]),
        ("先弹出2", [0,2], [], "输出2；结点3的入度从2减到1，仍不能入栈。", ["0","2"], ["1"]),
        ("再弹出1", [0,1], [], "输出1；结点3入度变0，入栈。", ["0","2","1"], ["3"]),
        ("弹出3", [0,1,2,3], [], "3使4的入度从1减到0，4入栈。", ["0","2","1","3"], ["4"]),
        ("弹出4", [0,1,2,3,4], [], "全部顶点输出；一种合法拓扑序是0、2、1、3、4。", ["0","2","1","3","4"], []),
    ]
    frames=[]
    for title,active,done,detail,out,stack in states:
        svg=svg_graph(coords,edges,labels,active,done,directed=True)
        panels=[panel("DAG：每条边从前驱指向后继",svg),panel("输出与栈", f'<div style="font-size:28px;line-height:1.5">已输出：{" → ".join(out) or "—"}<br>栈底 → 栈顶：{"，".join(stack) or "空"}<br>剩余入度随出栈更新</div>', detail)]
        frames.append(frame("拓扑排序：入度归零才入栈", title, panels, detail))
    write_page(6,9,frames)

    # B08 P8 — BST deletion using the inorder predecessor.
    coords={0:(425,55),1:(220,160),2:(640,160),3:(110,270),4:(330,270),5:(730,270)}
    edges=[(0,1),(0,2),(1,3),(1,4),(2,5)]
    states=[
        ("开始删除45", ["45","24","53","12","37","93"], [], [], "当前树满足左小右大；要删除的45有两个孩子。"),
        ("找到前驱37", ["45","24","53","12","37","93"], [0,4], [], "待删结点45的前驱，是其左子树最右结点37。"),
        ("把37复制到根", ["37","24","53","12","37","93"], [0], [], "只改根的值；原来位置上的37还在，暂时形成重复值。"),
        ("删除原位置的37", ["37","24","53","12","","93"], [0], [0,1,2,3,5], "原37是叶子，递归删除即可；中序仍递增。"),
    ]
    frames=[]
    for title,labels,active,done,detail in states:
        svg=svg_tree(coords,edges,labels,active,done)
        panels=[panel("删除前后的搜索树",svg),panel("指针变化", '<div style="font-size:29px;line-height:1.6">① 左子树向右找<br>② 前驱值复制到待删结点<br>③ 沿左子树删除原前驱</div>', detail)]
        frames.append(frame("BST 删除双孩子结点：用中序前驱替换", title, panels, detail))
    write_page(8,8,frames)

    # B09 P4 — insertion sort pass states.
    states=[
        ([49,38,65,97,76],0,"初始序列：已排序区间从第1个元素开始。"),
        ([38,49,65,97,76],1,"第2趟：38先存入data[0]，49右移，38放到位置1。"),
        ([38,49,65,97,76],2,"第3趟：65已不小于49，不移动。"),
        ([38,49,65,97,76],3,"第4趟：97已就位；本趟只有比较。"),
        ([38,49,65,76,97],4,"第5趟：76暂存，97右移，76插到65后面。"),
    ]
    frames=[]
    for vals,active,detail in states:
        panels=[panel("data[1..5]",row(vals,active=[active] if active else []),"黄色表示本趟待插入值"),
                panel("当前划分",f'<div style="font-size:30px;line-height:1.6">有序前缀：{"  ".join(map(str,vals[:max(1,active)]))}<br>待插入：{vals[active] if active else "—"}<br>未处理后缀：{ "  ".join(map(str,vals[active+1:])) if active+1<len(vals) else "空"}</div>',detail)]
        frames.append(frame("直接插入：每趟把一个元素插入有序前缀",f"第{active+1}趟" if active else "开始",panels,detail))
    write_page(9,4,frames)

    # B09 P10 — hole-filling partition around 49.
    states=[
        ([49,38,65,97,76,13,27],"low=1，high=7；49先存到哨兵data[0]。"),
        ([27,38,65,97,76,13,"□"],"从右找到27，填进左坑；新坑在位置7。"),
        ([27,38,65,97,76,13,65],"从左找到65，填进右坑；新坑移到位置3。"),
        ([27,38,13,97,76,"□",65],"从右找到13，填进左坑；新坑移到位置6。"),
        ([27,38,13,49,76,97,65],"97填进右坑；low与high在4相遇，哨兵49归位。"),
    ]
    frames=[]
    for i,(vals,detail) in enumerate(states):
        active=[vals.index("□")] if "□" in vals else ([3] if i==4 else [])
        panels=[panel("数组当前位置",row(vals,active=active),"□ 表示当前挖出的坑；data[0] 保存49"),
                panel("两端扫描",f'<div style="font-size:31px;line-height:1.6">low：{1 if i<2 else 3 if i<4 else 4}<br>high：{7 if i<2 else 3 if i==2 else 6 if i==3 else 4}<br>交替从右、从左找值填坑</div>',detail)]
        frames.append(frame("Partition：以49为枢轴，沿坑位交替填数",f"状态 {i}",panels,detail))
    write_page(9,10,frames)

    # B10 P5 — sift 3 down through the larger child 9.
    states=[
        ([1,3,5,7,9,8,6],"k=2，待下沉值3在位置2；左右孩子是7和9。",[1,4],[]),
        ([1,3,5,7,9,8,6],"i=4；比较孩子7、9，选择较大的9。",[1,4],[4]),
        ([1,9,5,7,3,8,6],"9上移到位置2；待下沉值3随k移到位置5。",[1,4],[1]),
        ([1,9,5,7,3,8,6],"把哨兵中的3放到位置5；本次调整结束。",[4],[1]),
    ]
    frames=[]
    for vals,detail,active,done in states:
        arr=row(vals,active=active,done=done)
        tree=svg_tree({0:(425,45),1:(230,145),2:(620,145),3:(130,250),4:(330,250),5:(520,250),6:(720,250)},[(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)],vals,active,done)
        panels=[panel("顺序表（下标从1起）",arr,"arr[0] 暂存待下沉值3"),panel("完全二叉树视图",tree,detail)]
        frames.append(frame("HeapAdjust：选较大的孩子，把它向上移",detail,panels,detail))
    write_page(10,5,frames)

    # B10 P10 — one merge shows how a right-side value accounts for many pairs.
    states=[
        ([2,4,6],[1,3,5],[],0,"左右段已分别排好序；i 指左段，j 指右段。"),
        ([2,4,6],[3,5],[1],3,"1先于2输出；左段2、4、6都比1大，一次加3。"),
        ([4,6],[5],[1,2,3],5,"取3时左段剩4、6，再加2；随后输出4。"),
        ([],[],[1,2,3,4,5,6],6,"取5时左段剩6，再加1；最终跨段逆序对共6对。"),
    ]
    frames=[]
    for left,right,out,count,detail in states:
        panels=[chain_panel("左段",left or ["—"],"起点 i"),chain_panel("右段",right or ["—"],"起点 j"),chain_panel("归并结果",out or ["—"],f"count = {count}")]
        frames.append(frame("归并计数：右段先出时，左段剩余值都构成逆序对",detail,panels,detail))
    write_page(10,10,frames)


if __name__ == "__main__":
    build()
    print("过程页规格已生成：B02、B03、B04、B05、B06、B08、B09、B10。")
