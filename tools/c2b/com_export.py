# com_export.py —— PowerPoint COM 导出与放映验证（路径一律 Windows 反斜杠）
# 子命令:
#   png  <课件目录> [outdir]        导出每页 PNG（1920x1080）
#   probe <课件目录> <页号> [outdir] 实际放映该页并逐击截图（真播放验证，非静态推断）
#   open <课件目录>                 只验证 PowerPoint 能无修复打开并读回动画结构
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
if os.environ.get('C2B_ENABLE_POWERPOINT_COM') != '1':
    raise SystemExit('此旧脚本仅用于隔离的 PowerPoint 诊断；本项目以 WPS 人工放映验收，请勿用 COM 结果判定交付。')
import pythoncom
import win32com.client

def to_win(p): return os.path.abspath(p).replace('/', '\\')

def png(lesson_dir, outdir=None):
    lesson_id = os.path.basename(lesson_dir)
    outdir = outdir or os.path.join(r'D:\Program Project\SpecialtyCourses\_tmp\c2b-opt', lesson_id, 'png')
    os.makedirs(outdir, exist_ok=True)
    app = win32com.client.Dispatch('PowerPoint.Application')
    pres = app.Presentations.Open(to_win(os.path.join(lesson_dir, f'{lesson_id}.pptx')), True, False, False)
    pres.Export(to_win(outdir), 'PNG', 1920, 1080)
    n = len(pres.Slides)
    pres.Close()
    print(f'PNG EXPORT OK -> {outdir} ({n} slides)')
    app.Quit()

def open_check(lesson_dir):
    lesson_id = os.path.basename(lesson_dir)
    app = win32com.client.Dispatch('PowerPoint.Application')
    pres = app.Presentations.Open(to_win(os.path.join(lesson_dir, f'{lesson_id}.pptx')), True, False, False)
    print(f'OPEN OK, slides={pres.Slides.Count}')
    for i in range(1, pres.Slides.Count + 1):
        sl = pres.Slides(i)
        ms = sl.TimeLine.MainSequence
        if ms.Count:
            first = ms.Item(1)
            print(f'  slide{i}: {ms.Count} 效果, 首效果触发={first.Timing.TriggerType} (2=onClick 3=withPrev) 目标={first.Shape.Name}')
    pres.Close()
    app.Quit()

def probe(lesson_dir, page, outdir=None, clicks=None):
    """真实放映验证：打开幻灯片放映，GotoSlide(page)，逐击 view.Next() 并全屏截图。"""
    import PIL.ImageGrab as ImageGrab
    lesson_id = os.path.basename(lesson_dir)
    outdir = outdir or os.path.join(r'D:\Program Project\SpecialtyCourses\_tmp\c2b-opt', lesson_id, f'probe-p{page}')
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith('.png'): os.remove(os.path.join(outdir, f))
    app = win32com.client.Dispatch('PowerPoint.Application')
    app.Visible = True
    print('opening...', flush=True)
    pres = app.Presentations.Open(to_win(os.path.join(lesson_dir, f'{lesson_id}.pptx')), True, False, True)  # WithWindow=True
    nclicks = clicks
    if nclicks is None:
        import glob as g, yaml as _y
        spec_f = os.path.join(lesson_dir, 'pages', f'p{int(page):02d}.yaml')
        nclicks = len(_y.safe_load(open(spec_f, encoding='utf-8'))['steps']) if os.path.exists(spec_f) else 0
    print('running slideshow...', flush=True)
    sw = pres.SlideShowSettings.Run()
    print('slideshow up', flush=True)
    view = sw.View
    time.sleep(1.5)
    view.GotoSlide(int(page))
    time.sleep(1.0)
    ImageGrab.grab().save(os.path.join(outdir, 'step0-入页.png'))
    print('step0 saved', flush=True)
    for k in range(1, nclicks + 1):
        view.Next()          # 推进一次点击（下一个动画步骤）
        time.sleep(0.9)
        ImageGrab.grab().save(os.path.join(outdir, f'step{k}-第{k}击.png'))
        print(f'step{k} saved', flush=True)
    view.Exit()
    pres.Close()
    app.Quit()
    print(f'PROBE OK -> {outdir} ({nclicks + 1} 帧)')

def video(lesson_dir, out_mp4=None, slide_secs=14):
    """对 -autoproof.pptx 变体做 CreateVideo 真实渲染（窗口无关，不会卡）。"""
    lesson_id = os.path.basename(lesson_dir)
    variant = os.path.join(r'D:\Program Project\SpecialtyCourses\_tmp\c2b-opt', lesson_id, f'{lesson_id}-autoproof.pptx')
    out_mp4 = out_mp4 or variant.replace('.pptx', '.mp4')
    app = win32com.client.Dispatch('PowerPoint.Application')
    pres = app.Presentations.Open(to_win(variant), True, False, False)
    pres.CreateVideo(to_win(out_mp4), False, slide_secs, 720, 30, 60)
    import time as _t
    # 状态: 3=Done, 4=Failed, 其余=进行中
    completed = False
    for _ in range(180):
        st = pres.CreateVideoStatus
        if st == 3:
            completed = True
            break
        if st == 4:
            pres.Close(); app.Quit()
            raise SystemExit('CreateVideo FAILED')
        _t.sleep(2)
    pres.Close()
    app.Quit()
    if not completed or not os.path.isfile(out_mp4) or os.path.getsize(out_mp4) == 0:
        raise SystemExit(f'CreateVideo 未在时限内成功完成：{out_mp4}')
    print(f'VIDEO OK -> {out_mp4}')

if __name__ == '__main__':
    cmd = sys.argv[1]
    pythoncom.CoInitialize()
    if cmd == 'png': png(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == 'open': open_check(sys.argv[2])
    elif cmd == 'video': video(sys.argv[2])
    elif cmd == 'probe': probe(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None,
                               int(sys.argv[5]) if len(sys.argv) > 5 else None)
