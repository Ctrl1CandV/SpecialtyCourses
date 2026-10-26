# finalize.py —— 幻灯片命名 + 原生箭头修补 + 点击动画时序注入
# 用法: python finalize.py <课件目录>
# 输入: <课件目录>/<课节>.pptx + manifest.json + pages/pNN.yaml（steps）
# 行为:
#   1) 按 manifest 顺序给 spTree 末尾 K 个形状命名（pNN:<id>），未命名的保持原样
#   2) 给标记 arrow 的原生线条确保 tailEnd（pptxgenjs 若已写则跳过）
#   3) 按 steps 生成 <p:timing>：每步一次点击，appear=淡入出场，hide=立即隐藏
# 幂等：重复运行先移除旧 <p:timing> 再注入。生成不检查内容——纯检查用 verify.py。
import sys, os, re, json, zipfile, shutil, glob
sys.stdout.reconfigure(encoding='utf-8')
from lxml import etree
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OPTIMIZED_ROOT = PROJECT_ROOT / '课程' / '课件' / 'C2' / 'C2-B-pro'

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
P = NS['p']; A = NS['a']
def q(tag):
    pre, local = tag.split(':')
    return f'{{{NS[pre]}}}{local}'

SHAPE_TAGS = {q('p:sp'), q('p:pic'), q('p:graphicFrame'), q('p:cxnSp'), q('p:grpSp')}

def make_el(xml):
    return etree.fromstring(xml)

def entrance_fade(cid, spid, node_type, dur=200):
    return make_el(f'''<p:par xmlns:p="{P}" xmlns:a="{A}"><p:cTn id="{cid}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="{node_type}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="{cid+1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set><p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{cid+2}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>''')

def exit_disappear(cid, spid, node_type):
    return make_el(f'''<p:par xmlns:p="{P}" xmlns:a="{A}"><p:cTn id="{cid}" presetID="1" presetClass="exit" presetSubtype="0" fill="hold" grpId="0" nodeType="{node_type}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="{cid+1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="hidden"/></p:to></p:set></p:childTnLst></p:cTn></p:par>''')

def click_group(cid, inner_els):
    grp = make_el(f'''<p:par xmlns:p="{P}" xmlns:a="{A}"><p:cTn id="{cid}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="{cid+1}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst/></p:cTn></p:par></p:childTnLst></p:cTn></p:par>''')
    holder = grp.find(f'{q("p:cTn")}/{q("p:childTnLst")}/{q("p:par")}/{q("p:cTn")}/{q("p:childTnLst")}')
    for e in inner_els:
        holder.append(e)
    return grp

def build_timing(steps_map):
    """steps_map: list of (appear_spids, hide_spids); returns p:timing element"""
    cid = [3]  # 1=root, 2=mainSeq
    def nid(n=1):
        v = cid[0]; cid[0] += n; return v
    groups = []
    animated_spids = []
    for appear, hide in steps_map:
        # 组 id 先于子效果分配（与 PowerPoint 自身写出的单调递增一致）
        gid = nid(2)
        inner = []
        first = True
        for spid in hide:
            inner.append(exit_disappear(nid(2), spid, 'clickEffect' if first else 'withEffect'))
            if spid not in animated_spids: animated_spids.append(spid)
            first = False
        for spid in appear:
            inner.append(entrance_fade(nid(3), spid, 'clickEffect' if first else 'withEffect'))
            if spid not in animated_spids: animated_spids.append(spid)
            first = False
        if not inner:
            continue
        groups.append(click_group(gid, inner))
    timing = make_el(f'''<p:timing xmlns:p="{P}" xmlns:a="{A}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst/></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>''')
    seq_children = timing.find(f'{q("p:tnLst")}/{q("p:par")}/{q("p:cTn")}/{q("p:childTnLst")}/{q("p:seq")}/{q("p:cTn")}/{q("p:childTnLst")}')
    for g in groups:
        seq_children.append(g)
    # 唯一性断言：cTn id 冲突会让 PowerPoint 静默丢弃效果
    ids = [c.get('id') for c in timing.iter(q('p:cTn'))]
    if len(ids) != len(set(ids)):
        dup = [i for i in set(ids) if ids.count(i) > 1]
        raise SystemExit(f'时序 id 冲突: {dup}')
    # bldLst：为每个被动画的形状补 bldP（与 PowerPoint 自身写法一致）
    if animated_spids:
        tnLst = timing.find(q('p:tnLst'))
        bld = etree.SubElement(timing, q('p:bldLst'))
        for spid in animated_spids:
            bp = etree.SubElement(bld, q('p:bldP'))
            bp.set('spid', str(spid)); bp.set('grpId', '0'); bp.set('animBg', '1')
    return timing, len(groups)

def finalize(lesson_dir):
    lesson_dir = Path(lesson_dir).resolve()
    if lesson_dir.parent != OPTIMIZED_ROOT.resolve() or not re.fullmatch(r'C2-B-(0[1-9]|10)', lesson_dir.name):
        raise SystemExit(f'拒绝操作该目录；只允许处理 {OPTIMIZED_ROOT}/C2-B-01…C2-B-10：{lesson_dir}')
    lesson_id = lesson_dir.name
    pptx_path = os.path.join(lesson_dir, f'{lesson_id}.pptx')
    manifest = json.load(open(os.path.join(lesson_dir, 'manifest.json'), encoding='utf-8'))
    pages = {}
    for f in glob.glob(os.path.join(lesson_dir, 'pages', 'p*.yaml')):
        s = yaml.safe_load(open(f, encoding='utf-8'))
        pages[s['page']] = s

    tmp = pptx_path + '.tmp'
    zin = zipfile.ZipFile(pptx_path, 'r')
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    report = []
    for item in zin.infolist():
        data = zin.read(item.filename)
        m = re.match(r'ppt/slides/slide(\d+)\.xml$', item.filename)
        if m:
            idx = int(m.group(1))
            root = etree.fromstring(data)
            man = manifest['slides'][idx - 1]
            spTree = root.find(f'{q("p:cSld")}/{q("p:spTree")}')
            shapes = [c for c in spTree if c.tag in SHAPE_TAGS]
            entries = man['entries']
            if len(shapes) != len(entries):
                raise SystemExit(f'{item.filename}: 形状数 {len(shapes)} != manifest 条目 {len(entries)}，构建器与清单不一致；为避免错命名已中止')
            tail = shapes[len(shapes) - len(entries):]
            name2id = {}
            for shp, ent in zip(tail, entries):
                cnv = shp.find(f'{q("p:nvSpPr")}/{q("p:cNvPr")}')
                if cnv is None:
                    cnv = shp.find(f'{q("p:nvPicPr")}/{q("p:cNvPr")}')
                if cnv is None:
                    cnv = shp.find(f'{q("p:nvGraphicFramePr")}/{q("p:cNvPr")}')
                if cnv is None:
                    raise SystemExit(f'{item.filename}: 找不到 cNvPr')
                if ent.get('id') or ent.get('name'):
                    cnv.set('name', ent.get('id') or ent['name'])
                if ent.get('id'):
                    name2id[ent['id']] = cnv.get('id')
                # 原生箭头修补
                if ent.get('arrow'):
                    spPr = shp.find(f'{q("p:spPr")}')
                    ln = spPr.find(q('a:ln')) if spPr is not None else None
                    if ln is not None and ln.find(q('a:tailEnd')) is None:
                        te = etree.SubElement(ln, q('a:tailEnd')); te.set('type', 'triangle')
            # 时序注入
            page_spec = pages.get(man['page'])
            if page_spec and (page_spec.get('steps')):
                old = root.find(q('p:timing'))
                if old is not None: root.remove(old)
                steps_map = []
                for step_no, st in enumerate(page_spec['steps'], 1):
                    ap, hi = [], []
                    for eid in st.get('hide', []):
                        key = f"p{man['page']:02d}:{eid}"
                        if key not in name2id: raise SystemExit(f"slide{idx} steps[{step_no}].hide 引用未定义元素 {key}")
                        hi.append(name2id[key])
                    for eid in st.get('appear', []):
                        key = f"p{man['page']:02d}:{eid}"
                        if key not in name2id: raise SystemExit(f"slide{idx} steps[{step_no}].appear 引用未定义元素 {key}")
                        ap.append(name2id[key])
                    if not ap and not hi: raise SystemExit(f"slide{idx} steps[{step_no}] 没有 appear/hide 动作")
                    if len(ap) != len(set(ap)) or len(hi) != len(set(hi)) or set(ap) & set(hi):
                        raise SystemExit(f"slide{idx} steps[{step_no}] 含重复或冲突目标")
                    steps_map.append((ap, hi))
                timing, ngroups = build_timing(steps_map)
                root.append(timing)
                report.append(f'slide{idx}: {len(name2id)} 命名对象, {ngroups} 个点击步骤')
            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(item, data)
    zin.close(); zout.close()
    shutil.move(tmp, pptx_path)
    for r in report: print(r)
    print(f'FINALIZE OK -> {pptx_path}')

if __name__ == '__main__':
    finalize(sys.argv[1])
