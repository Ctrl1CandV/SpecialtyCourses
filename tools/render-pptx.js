// render-pptx.js —— PPT 渲染引擎（只管布局与样式，不碰内容）
// 内容来源：课件目录下与 pptx 同名的 deck.yaml（结构化幻灯片规格）
// 用法: node render-pptx.js <deck.yaml> [输出.pptx]
// 示例: node render-pptx.js "..\课件\C1\C1-A-01\deck.yaml"
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const PptxGenJS = require('pptxgenjs');

// ================= 全局样式（唯一权威，禁止在内容侧覆盖） =================
const S = {
  ink: '1F2329',      // 正文
  blue: '1F4E9C',     // 主题（仅标题与关键词）
  red: 'C0392B',      // 强调（仅角标与极少量强调）
  gray: '8A9099',     // 次要文字
  line: 'D8DBE0',     // 表格线
  headBg: 'F5F6F7',   // 表头底
  codeBg: 'F5F6F7',   // 代码底
  font: '微软雅黑',
  codeFont: 'Consolas',
};
const W = 13.333, H = 7.5;          // 16:9
const MX = 0.9;                      // 左右边距
const CW = W - MX * 2;               // 内容宽
const TOP_DEF = 1.05;                // 顶部安全区默认值（避开底图顶部色带，色带高约0.74in）
let TOP = TOP_DEF;                   // 可被 deck.meta.topSafe 覆盖（如题集勾画底图左上角有校徽，需下移）
const BODY_TOP = 2.62;               // 正文起始
const FOOT_Y = 6.58;                 // 页脚（底图底部色带从约7.10in开始，页脚须在其上方）
const CONTENT_BOTTOM = 6.42;         // 内容块可用底边界
let BG = path.resolve(__dirname, '..', 'assets', '底图.jpg'); // 可被 deck.meta.background 覆盖

// ================= 工具 =================
function parseRuns(text, base) {
  // 解析 **加粗** 为 runs
  const runs = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push(Object.assign({ text: text.slice(last, m.index) }, base));
    runs.push(Object.assign({ text: m[1], options: { bold: true } }, base));
    last = m.index + m[0].length;
  }
  if (last < text.length) runs.push(Object.assign({ text: text.slice(last) }, base));
  return runs.length ? runs : [Object.assign({ text: String(text) }, base)];
}
function textLen(text) { return String(text).replace(/\*\*/g, '').length; }
function estLines(text, pt, width) {
  const cw = (pt / 72) * 1.06; // 中文近似字宽
  const per = Math.max(1, Math.floor(width / cw));
  let n = 0;
  for (const seg of String(text).split('\n')) n += Math.max(1, Math.ceil(textLen(seg) / per));
  return n;
}

// ================= 页面渲染 =================
function baseSlide(pptx, deck, pageNo, total) {
  const slide = pptx.addSlide();
  slide.background = { path: BG, sizing: { type: 'cover', w: '100%', h: '100%' } };
  // 页脚：仅页码（底图自带机构宣传，页面上不再打机构标签）
  slide.addText(pageNo + ' / ' + total, { x: W - 2, y: FOOT_Y, w: 2 - MX + 0.5, h: 0.35, fontSize: 10, fontFace: S.font, color: S.gray, align: 'right' });
  return slide;
}

function renderHeader(slide, sl) {
  // kicker：小字、蓝色、加粗
  if (sl.kicker) {
    slide.addText(sl.kicker, { x: MX, y: TOP, w: CW, h: 0.4, fontSize: 14, fontFace: S.font, color: S.blue, bold: true, align: 'left' });
  }
  // title：大字、黑色加粗（去AI味：标题用黑色，减少彩色噪音）
  if (sl.title) {
    slide.addText(sl.title, { x: MX, y: TOP + 0.42, w: CW, h: 0.8, fontSize: 28, fontFace: S.font, color: S.ink, bold: true, align: 'left' });
  }
}

function renderBlocks(slide, sl, startY) {
  let y = startY;
  const avail = CONTENT_BOTTOM - startY;
  // 预估总高度，超了就整体缩字号
  let need = 0;
  for (const b of (sl.blocks || [])) need += blockHeight(b, CW);
  const scale = need > avail ? Math.max(0.78, avail / need) : 1;

  for (const b of (sl.blocks || [])) {
    y = renderBlock(slide, b, y, scale);
  }
  return y;
}

function blockHeight(b, width) {
  switch (b.type) {
    case 'bullets': {
      let n = 0;
      for (const it of b.items) n += estLines(it, 18, width - 0.4) ;
      return n * 18 / 72 * 1.5 + b.items.length * 0.08 + 0.15;
    }
    case 'table': {
      const rows = (b.rows ? b.rows.length : 0) + (b.head ? 1 : 0);
      return rows * 0.46 + 0.2;
    }
    case 'code': {
      const lines = String(b.text).split('\n').length;
      return Math.max(0.6, lines * 0.26 + 0.35);
    }
    case 'note': return estLines(b.text, 15, width) * 15 / 72 * 1.5 + 0.2;
    case 'text': return estLines(b.text, b.size || 18, width) * (b.size || 18) / 72 * 1.5 + 0.2;
    case 'gap': return b.h || 0.2;
    case 'image': {
      const iw = b.w || (CW * 0.6);
      const ih = b.h || (iw * 0.66);
      return Math.max(ih, 0.6) + 0.2;
    }
    default: return 0.4;
  }
}

function renderBlock(slide, b, y, scale) {
  switch (b.type) {
    case 'bullets': {
      const pt = Math.round(18 * scale);
      for (const it of b.items) {
        const clean = String(it).replace(/\*\*/g, '');
        const lines = estLines(it, pt, CW - 0.42);
        const h = lines * pt / 72 * 1.5 + 0.06;
        const runs = parseRuns(it, { fontSize: pt, fontFace: S.font, color: S.ink });
        slide.addText([{ text: '•  ', options: { fontSize: pt, fontFace: S.font, color: S.blue, bold: true } }, ...runs],
          { x: MX + 0.08, y, w: CW - 0.1, h, align: 'left', valign: 'top', lineSpacingMultiple: 1.15 });
        y += h + 0.08;
      }
      return y + 0.1;
    }
    case 'table': {
      const headRow = b.head ? [b.head.map(t => ({ text: String(t), options: { bold: true, color: S.blue, fill: { color: S.headBg } } }))] : [];
      const bodyRows = (b.rows || []).map(r => r.map(c => ({ text: String(c), options: { color: S.ink, fill: { color: 'FFFFFF' } } })));
      const all = headRow.concat(bodyRows);
      const rowH = 0.46;
      slide.addTable(all, {
        x: MX, y, w: CW, rowH,
        fontSize: Math.round(15 * scale), fontFace: S.font,
        align: b.align || 'center', valign: 'middle',
        border: { type: 'solid', pt: 0.75, color: S.line },
        autoPage: false,
        ...(Array.isArray(b.colW) && b.colW.length ? { colW: b.colW } : {}),
      });
      return y + all.length * rowH + 0.25;
    }
    case 'code': {
      const lines = String(b.text).split('\n');
      const ch = Math.max(0.6, lines.length * 0.26 + 0.35);
      slide.addShape('rect', { x: MX, y, w: CW, h: ch, fill: { color: S.codeBg }, line: { color: S.line, width: 0.75 } });
      slide.addText(String(b.text), {
        x: MX + 0.28, y: y + 0.12, w: CW - 0.56, h: ch - 0.24,
        fontFace: S.codeFont, fontSize: Math.round(13.5 * scale), color: S.ink,
        align: 'left', valign: 'top', lineSpacingMultiple: 1.25,
      });
      return y + ch + 0.22;
    }
    case 'note': {
      const pt = Math.round(15 * scale);
      const lines = estLines(b.text, pt, CW);
      const h = lines * pt / 72 * 1.5 + 0.08;
      slide.addText(String(b.text), { x: MX, y, w: CW, h, fontSize: pt, fontFace: S.font, color: S.gray, align: 'left', valign: 'top' });
      return y + h + 0.12;
    }
    case 'text': {
      const pt = Math.round((b.size || 18) * scale);
      const lines = estLines(b.text, pt, CW);
      const h = lines * pt / 72 * 1.5 + 0.08;
      const runs = parseRuns(b.text, { fontSize: pt, fontFace: S.font, color: b.color === 'blue' ? S.blue : (b.color === 'red' ? S.red : S.ink), bold: !!b.bold });
      slide.addText(runs, { x: MX, y, w: CW, h, align: b.align || 'left', valign: 'top' });
      return y + h + 0.14;
    }
    case 'gap': return y + (b.h || 0.2);
    case 'image': {
      // 图片块：支持 b.src（路径，相对于项目根或绝对）或 b.path（旧称兼容）
      const src = b.src || b.path;
      if (!src) return y + 0.4;
      const imgPath = path.isAbsolute(src) ? src : path.resolve(__dirname, '..', src);
      if (!fs.existsSync(imgPath)) {
        slide.addText('[图片未找到: ' + src + ']', { x: MX, y, w: CW, h: 0.4, fontSize: 14, fontFace: S.font, color: S.red, align: 'center' });
        return y + 0.6;
      }
      const iw = b.w || (CW * 0.6);
      const ih = b.h || (iw * 0.66);
      const ix = b.align === 'center' ? (W - iw) / 2 : MX;
      const sizing = b.fit === 'contain'
        ? { type: 'contain', w: iw, h: ih }
        : { type: 'cover', w: iw, h: ih };
      slide.addImage({ path: imgPath, x: ix, y, w: iw, h: ih, sizing });
      return y + ih + 0.2;
    }
    default: return y + 0.4;
  }
}

function renderCover(pptx, deck, sl, pageNo, total) {
  const slide = baseSlide(pptx, deck, pageNo, total);
  const cy = 2.35;
  if (sl.kicker) slide.addText(sl.kicker, { x: 0, y: cy, w: W, h: 0.5, fontSize: 18, fontFace: S.font, color: S.blue, bold: true, align: 'center' });
  slide.addText(sl.title || '', { x: 0, y: cy + 0.75, w: W, h: 1.25, fontSize: 48, fontFace: S.font, color: S.ink, bold: true, align: 'center' });
  if (sl.subtitle) slide.addText(sl.subtitle, { x: 0, y: cy + 2.15, w: W, h: 0.6, fontSize: 20, fontFace: S.font, color: S.ink, align: 'center' });
  if (sl.meta) slide.addText(sl.meta, { x: 0, y: cy + 2.95, w: W, h: 0.5, fontSize: 14, fontFace: S.font, color: S.gray, align: 'center' });
}

function renderTransition(pptx, deck, sl, pageNo, total) {
  const slide = baseSlide(pptx, deck, pageNo, total);
  const cy = 3.0;
  if (sl.kicker) slide.addText(sl.kicker, { x: 0, y: cy - 0.75, w: W, h: 0.45, fontSize: 16, fontFace: S.font, color: S.blue, bold: true, align: 'center' });
  slide.addText(sl.title || '', { x: 0, y: cy, w: W, h: 0.95, fontSize: 38, fontFace: S.font, color: S.ink, bold: true, align: 'center' });
  if (sl.subtitle) slide.addText(sl.subtitle, { x: 0, y: cy + 1.05, w: W, h: 0.55, fontSize: 17, fontFace: S.font, color: S.gray, align: 'center' });
}

function renderBoard(pptx, deck, sl, pageNo, total) {
  const slide = baseSlide(pptx, deck, pageNo, total);
  renderHeader(slide, sl);
  if (sl.task) {
    slide.addText(sl.task, { x: MX, y: TOP + 1.35, w: CW, h: 0.75, fontSize: 16, fontFace: S.font, color: S.ink, align: 'left', valign: 'top' });
  }
  // 板书区：大空白 + 虚线框（底部避开底图色带）
  const by = 3.3;
  slide.addShape('rect', { x: MX, y: by, w: CW, h: 3.05, fill: { color: 'FFFFFF' }, line: { color: 'B9C0C9', width: 1, dashType: 'dash' } });
  slide.addText('此处板书推演', { x: MX, y: by + 2.55, w: CW, h: 0.4, fontSize: 12, fontFace: S.font, color: S.gray, align: 'right' });
}

function renderContent(pptx, deck, sl, pageNo, total) {
  const slide = baseSlide(pptx, deck, pageNo, total);
  // 角标（右上角，与标题对齐）
  if (sl.badge) {
    slide.addShape('roundRect', { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fill: { color: 'FFFFFF' }, line: { color: S.red, width: 1.2 }, rectRadius: 0.08 });
    slide.addText(sl.badge, { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fontSize: 13, fontFace: S.font, color: S.red, bold: true, align: 'center', valign: 'middle' });
  }
  renderHeader(slide, sl);
  renderBlocks(slide, sl, BODY_TOP);
}

// ================= 主流程 =================
async function main() {
  const file = process.argv[2];
  if (!file) { console.error('用法: node render-pptx.js <deck.yaml> [输出.pptx]'); process.exit(1); }
  const yamlPath = path.resolve(file);
  const outPath = process.argv[3] ? path.resolve(process.argv[3]) : path.join(path.dirname(yamlPath), path.basename(path.dirname(yamlPath)) + '.pptx');

  const deck = yaml.load(fs.readFileSync(yamlPath, 'utf8'));
  const slides = deck.slides || [];
  if (!slides.length) { console.error('deck.yaml 中没有 slides'); process.exit(1); }

  // deck 级覆盖：底图与顶部安全区（默认课程底图不变，题集勾画等专用底图走 meta.background）
  if (deck.meta && deck.meta.background) {
    BG = path.isAbsolute(deck.meta.background) ? deck.meta.background : path.resolve(__dirname, '..', deck.meta.background);
  }
  if (deck.meta && deck.meta.topSafe) TOP = deck.meta.topSafe;
  if (!fs.existsSync(BG)) { console.error('未找到底图: ' + BG); process.exit(1); }

  const pptx = new PptxGenJS();
  pptx.defineLayout({ name: 'W16x9', width: W, height: H });
  pptx.layout = 'W16x9';
  pptx.author = (deck.meta && deck.meta.instructor) || '';
  pptx.title = (deck.meta && deck.meta.title) || '';

  slides.forEach((sl, i) => {
    const pageNo = i + 1, total = slides.length;
    switch (sl.type) {
      case 'cover': return renderCover(pptx, deck, sl, pageNo, total);
      case 'transition': return renderTransition(pptx, deck, sl, pageNo, total);
      case 'board': return renderBoard(pptx, deck, sl, pageNo, total);
      default: return renderContent(pptx, deck, sl, pageNo, total);
    }
  });

  await pptx.writeFile({ fileName: outPath });
  console.log('OK -> ' + outPath + ' (' + slides.length + ' slides)');
}

main().catch(e => { console.error(e); process.exit(1); });
