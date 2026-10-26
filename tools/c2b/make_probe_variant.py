# make_probe_variant.py —— 从交付 pptx 派生"自动播放验证版"
# 转换方式与 PowerPoint 自身"之后上一动画之后自动播放"的写法一致：
#   mainSeq 的多个点击组合并为一个组；每个效果的 stCondLst delay = 原组序号 × STEP_MS。
# 该副本只用于 PowerPoint CreateVideo 真实渲染动画进程，交付文件不受影响。
import sys, os, re, zipfile
sys.stdout.reconfigure(encoding='utf-8')
from lxml import etree

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
def q(t): return f'{{{P}}}{t.split(":")[1]}'

def main(lesson_dir, out_path=None, step_ms=1200):
    lesson_id = os.path.basename(lesson_dir)
    src = os.path.join(lesson_dir, f'{lesson_id}.pptx')
    out_path = out_path or os.path.join(r'D:\Program Project\SpecialtyCourses\_tmp\c2b-opt', lesson_id, f'{lesson_id}-autoproof.pptx')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    zin = zipfile.ZipFile(src)
    n_timed = 0
    zout = zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        m = re.match(r'ppt/slides/slide(\d+)\.xml$', item.filename)
        if m and b'<p:timing>' in data:
            root = etree.fromstring(data)
            seq = root.find(f'{q("p:timing")}//{q("p:seq")}')
            main_ctn = seq.find(q('p:cTn'))
            groups = main_ctn.find(q('p:childTnLst'))
            effect_pars = []
            for k, g in enumerate(groups):
                for lvl in g.iter(q('p:par')):
                    # 只取效果层（其父是内层 childTnLst，且带 presetClass）
                    ctn = lvl.find(q('p:cTn'))
                    if ctn is not None and ctn.get('presetClass'):
                        cond = ctn.find(f'{q("p:stCondLst")}/{q("p:cond")}')
                        if cond is not None:
                            cond.set('delay', str(k * step_ms))
                        effect_pars.append(lvl)
            # 重建 single group
            new_child = main_ctn.find(q('p:childTnLst'))
            for child in list(new_child):
                new_child.remove(child)
            single = etree.SubElement(new_child, q('p:par'))
            gctn = etree.SubElement(single, q('p:cTn'))
            gctn.set('id', '500')  # 唯一即可，避开 root/mainSeq 的 1/2
            gctn.set('fill', 'hold')
            st = etree.SubElement(gctn, q('p:stCondLst'))
            c0 = etree.SubElement(st, q('p:cond')); c0.set('delay', '0')
            ch = etree.SubElement(gctn, q('p:childTnLst'))
            for ep in effect_pars:
                ch.append(ep)
            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            n_timed += 1
        zout.writestr(item, data)
    zin.close(); zout.close()
    print(f'PROBE VARIANT -> {out_path} (动画页 {n_timed}, 效果步进 {step_ms}ms)')

if __name__ == '__main__':
    main(sys.argv[1])
