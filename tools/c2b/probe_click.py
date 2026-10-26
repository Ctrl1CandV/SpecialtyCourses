# probe_click.py —— 真实放映逐击截图（经 view.Next 进入目标页，从初始状态开始）
# 用法: python probe_click.py <课件目录> <页号> [前页号]
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
if os.environ.get('C2B_ENABLE_POWERPOINT_COM') != '1':
    raise SystemExit('此旧脚本仅用于隔离的 PowerPoint 诊断；本项目以 WPS 人工放映验收，请勿用 COM 结果判定交付。')
import pythoncom, win32com.client
pythoncom.CoInitialize()
BS = chr(92)
import PIL.ImageGrab as ImageGrab
lesson_dir = os.path.abspath(sys.argv[1]); page = int(sys.argv[2])
prev_page = int(sys.argv[3]) if len(sys.argv) > 3 else page - 1
lesson_id = os.path.basename(lesson_dir)
outdir = os.path.join(r'D:\Program Project\SpecialtyCourses\_tmp\c2b-opt', lesson_id, f'probe-p{page}')
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    if f.endswith('.png'): os.remove(os.path.join(outdir, f))
import yaml
spec = os.path.join(lesson_dir, 'pages', f'p{page:02d}.yaml')
nclicks = len(yaml.safe_load(open(spec, encoding='utf-8'))['steps']) if os.path.exists(spec) else 0
app = win32com.client.Dispatch('PowerPoint.Application')
pres = app.Presentations.Open(os.path.join(lesson_dir, f'{lesson_id}.pptx').replace('/', BS), True, False, False)
app.Visible = True
sw = pres.SlideShowSettings.Run()
view = sw.View
time.sleep(1.5)
if prev_page >= 1:
    view.GotoSlide(prev_page); time.sleep(0.6)
    view.Next()                     # 进入目标页（初始状态）
else:
    view.GotoSlide(page)
time.sleep(1.2)
ImageGrab.grab().save(os.path.join(outdir, 'step0-入页.png')); print('step0', flush=True)
for k in range(1, nclicks + 1):
    view.Next(); time.sleep(1.0)
    ImageGrab.grab().save(os.path.join(outdir, f'step{k}.png')); print(f'step{k}', flush=True)
try: view.Exit()
except Exception: pass
try: pres.Close()
except Exception: pass
app.Quit()
print('PROBE-DONE', flush=True)
