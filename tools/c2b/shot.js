// shot.js —— 页面规格 → HTML → Chrome headless 透明 PNG
// 用法: node shot.js <课件目录> [--audit] [--only=pNN,pNN]
// 读取 <课件目录>/pages/pNN.yaml，产出:
//   <课件目录>/assets/<lesson>-pNN-fixed-<id>.png   固定层元素
//   <课件目录>/assets/<lesson>-pNN-<id>.png          动画层元素（透明、按 box 裁剪）
//   <课件目录>/html/pNN-<id>.html                    HTML 源（留存）
// --audit: 只做溢出自检（每页 HTML 内嵌脚本报告 scroll 溢出），不截图
'use strict';
const fs = require('fs');
const path = require('path');
const { PROJECT_ROOT, assertOptimizedLessonDir } = require('./paths.js');
const yaml = require(path.join(PROJECT_ROOT, 'tools', 'node_modules', 'js-yaml'));
const { execFileSync } = require('child_process');
const { elementDoc, PPI, inch2px } = require('./house.js');
const { pathToFileURL } = require('url');

function findBrowser() {
  const candidates = [
    process.env.C2B_CHROME,
    path.join(process.env.PROGRAMFILES || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
    path.join(process.env['PROGRAMFILES(X86)'] || 'C:/Program Files (x86)', 'Google/Chrome/Application/chrome.exe'),
    path.join(process.env.PROGRAMFILES || 'C:/Program Files', 'Microsoft/Edge/Application/msedge.exe'),
    path.join(process.env['PROGRAMFILES(X86)'] || 'C:/Program Files (x86)', 'Microsoft/Edge/Application/msedge.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate));
}

function main() {
  if (!process.argv[2]) throw new Error('用法: node shot.js <优化版课节目录> [--audit] [--only=pNN,pNN]');
  const lessonDir = assertOptimizedLessonDir(process.argv[2]);
  const argAudit = process.argv.includes('--audit');
  const onlyArg = (process.argv.find(a => a.startsWith('--only=')) || '').slice(7);
  const only = onlyArg ? onlyArg.split(',') : null;
  const lessonId = path.basename(lessonDir);
  const pagesDir = path.join(lessonDir, 'pages');
  const assetsDir = path.join(lessonDir, 'assets');
  const htmlDir = path.join(lessonDir, 'html');
  if (!argAudit) {
    fs.mkdirSync(assetsDir, { recursive: true });
    fs.mkdirSync(htmlDir, { recursive: true });
  }
  const specs = fs.readdirSync(pagesDir).filter(f => /^p\d+\.yaml$/.test(f)).sort();
  if (!specs.length) { console.log('没有 pages/pNN.yaml'); return; }
  const browser = findBrowser();
  if (!browser) throw new Error('找不到 Chrome 或 Edge；可用环境变量 C2B_CHROME 指定浏览器路径。');

  let failures = [];
  for (const f of specs) {
    const page = yaml.load(fs.readFileSync(path.join(pagesDir, f), 'utf8'));
    const pn = String(page.page).padStart(2, '0');
    if (only && !only.includes(pn)) continue;
    const els = []
      .concat((page.fixed || []).map(e => ({ ...e, layer: 'fixed' })))
      .concat((page.anim || []).map(e => ({ ...e, layer: 'anim' })));
    for (const el of els) {
      const box = el.box;                       // [x,y,w,h] inches
      if (!box || box.length !== 4) throw new Error(`${f} 元素 ${el.id} 缺 box`);
      if (!/^[A-Za-z0-9_-]+$/.test(el.id || '')) throw new Error(`${f} 元素 id 只能包含英文、数字、下划线和连字符`);
      if (!box.every(Number.isFinite) || box[2] <= 0 || box[3] <= 0 || box[0] < 0 || box[1] < 1.05 || box[0] + box[2] > 13.313 || box[1] + box[3] > 6.44) {
        throw new Error(`${f}/${el.id} 超出幻灯片正文安全区: ${JSON.stringify(box)}`);
      }
      const wpx = inch2px(box[2]), hpx = inch2px(box[3]);
      if (el.component === 'image' && el.props && el.props.src) {
        const srcPath = path.resolve(lessonDir, el.props.src);
        if (!fs.existsSync(srcPath)) throw new Error(`${f}/${el.id} 找不到图片: ${srcPath}`);
        el.props.srcAbs = pathToFileURL(srcPath).href;
      }
      const doc = elementDoc(el, [wpx, hpx]);
      const outName = el.layer === 'fixed' ? `${lessonId}-p${pn}-fixed-${el.id}.png` : `${lessonId}-p${pn}-${el.id}.png`;
      const outPath = path.join(assetsDir, outName);
      const htmlPath = path.join(htmlDir, `p${pn}-${el.id}.html`);
      const url = argAudit
        ? 'data:text/html;base64,' + Buffer.from(doc, 'utf8').toString('base64')
        : pathToFileURL(htmlPath).href;
      if (argAudit) {
        // 只读 DOM 容量检查：data URL 避免写入 HTML 或 PNG。
        const dom = execFileSync(browser, [
          '--headless=new', '--disable-gpu', '--hide-scrollbars',
          `--window-size=${wpx},${hpx}`, '--virtual-time-budget=2000', '--dump-dom', url,
        ], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
        const m = dom.match(/id="audit-result"[^>]*>([^<]*)</);
        const verdict = m ? m[1] : 'AUDIT-MISSING';
        console.log(`p${pn}/${el.id}: ${verdict}`);
        if (!/OK$/.test(verdict)) failures.push(`${lessonId} p${pn}/${el.id}: ${verdict}`);
      } else {
        fs.writeFileSync(htmlPath, doc, 'utf8');
        execFileSync(browser, [
          '--headless=new', '--disable-gpu', '--hide-scrollbars',
          `--window-size=${wpx},${hpx}`, '--default-background-color=00000000',
          `--screenshot=${outPath}`, url,
        ], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
        console.log(`OK ${outName} (${wpx}x${hpx})`);
      }
    }
  }
  if (argAudit) {
    if (failures.length) { console.error('\nAUDIT FAILURES:\n' + failures.join('\n')); process.exit(1); }
    console.log('\nAUDIT ALL OK');
  }
}
main();
