// render-v2.js —— C2-B 优化版 PPT 构建器
// 输入: <课件目录>/deck.yaml（页序与标题权威） + <课件目录>/pages/pNN.yaml（混合页版面/动画规格）
// 输出: <课件目录>/<课节>.pptx + manifest.json（形状命名与顺序，供 finalize.py 注入动画）
// 与 tools/render-pptx.js 的关系: 原生页沿用同一套版式常量与画法（视觉一致），
//   但行高估算更保守，且任何溢出都会作为构建错误报告（不再静默缩放/裁切）。
// 本工具只负责生成；纯检查用 verify.py（只读）。
'use strict';
const fs = require('fs');
const path = require('path');
const { PROJECT_ROOT, assertOptimizedLessonDir } = require('./paths.js');
const yaml = require(path.join(PROJECT_ROOT, 'tools', 'node_modules', 'js-yaml'));
const PptxGenJS = require(path.join(PROJECT_ROOT, 'tools', 'node_modules', 'pptxgenjs'));
const { CANVAS, COLORS, estLines, estTextHeight } = require('./house.js');

const W = CANVAS.W, H = CANVAS.H, MX = CANVAS.MX, TOP = CANVAS.TOP,
  BODY_TOP = CANVAS.BODY_TOP, FOOT_Y = CANVAS.FOOT_Y, CONTENT_BOTTOM = CANVAS.CONTENT_BOTTOM;
const CW = W - MX * 2;
const FONT = '微软雅黑', CODE_FONT = 'Consolas';

function parseRuns(text, base) {
  const runs = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  const t = String(text);
  while ((m = re.exec(t)) !== null) {
    if (m.index > last) runs.push(Object.assign({ text: t.slice(last, m.index) }, base));
    runs.push(Object.assign({ text: m[1], options: { bold: true } }, base));
    last = m.index + m[0].length;
  }
  if (last < t.length) runs.push(Object.assign({ text: t.slice(last) }, base));
  return runs.length ? runs : [Object.assign({ text: t }, base)];
}
const strip = s => String(s).replace(/\*\*/g, '');

// ================= 溢出登记 =================
const overflowReport = [];
function reportOverflow(lesson, pageNo, what, detail) {
  overflowReport.push(`${lesson} P${pageNo}: ${what} ${detail}`);
}
function checkInContentArea(lesson, pageNo, id, box, what) {
  const [x, y, w, h] = box;
  if (x < MX - 0.06 || x + w > W - MX + 0.06 || y < TOP - 0.02 || y + h > FOOT_Y + 0.02) {
    reportOverflow(lesson, pageNo, `[${id}] ${what} 超出内容安全区`, `box=(${x.toFixed(2)},${y.toFixed(2)},${w.toFixed(2)},${h.toFixed(2)}) 安区 x:[${MX},${(W - MX).toFixed(2)}] y:[${TOP},${FOOT_Y}]`);
  }
}

// ================= 原生块渲染（v1 同款画法 + 保守估行） =================
function blockHeight(b, width) {
  switch (b.type) {
    case 'bullets': {
      let n = 0;
      const pt = b.size || 18;
      for (const it of b.items) n += estLines(it, pt, width - 0.42);
      return n * pt / 72 * 1.5 + b.items.length * 0.08 + 0.15;
    }
    case 'table': {
      const rows = (b.rows ? b.rows.length : 0) + (b.head ? 1 : 0);
      return rows * (b.rowH || 0.46) + 0.2;
    }
    case 'code': {
      if (typeof b.text !== 'string' || !b.text.trim()) return NaN;
      const lines = String(b.text).replace(/\n+$/, '').split('\n');
      const pt = b.size || 13.5;
      const per = pt >= 13 ? 0.30 : (pt <= 11 ? 0.23 : 0.25); // 11pt 代码预留较小但仍含上下内边距
      return Math.max(0.6, lines.length * per + 0.35);
    }
    case 'note': { const pt = b.size || 15; return estLines(b.text, pt, width) * pt / 72 * 1.5 + 0.2; }
    case 'text': return estLines(b.text, b.size || 18, width) * (b.size || 18) / 72 * 1.5 + 0.2;
    case 'gap': return b.h || 0.2;
    case 'image': {
      const iw = b.w || (CW * 0.6);
      const ih = b.h || (iw * 0.66);
      return Math.max(ih, 0.6) + 0.2;
    }
    case 'diagram': return (b.h || 1.5) + 0.2;
    default: return 0.4;
  }
}

function blockTail(b) {
  return ({ bullets: 0.10, table: 0.25, code: 0.22, note: 0.12, text: 0.14, image: 0.20, diagram: 0.20, gap: 0 })[b.type] || 0;
}

function renderBlock(pptx, slide, b, y, scale, man, x = MX, width = CW) {
  switch (b.type) {
    case 'bullets': {
      const pt = Math.round((b.size || 18) * scale);
      for (const it of b.items) {
        const clean = strip(it);
        const lines = estLines(it, pt, width - 0.42);
        const h = lines * pt / 72 * 1.5 + 0.06;
        slide.addText([{ text: '•  ', options: { fontSize: pt, fontFace: FONT, color: COLORS.blue, bold: true } }, ...parseRuns(it, { fontSize: pt, fontFace: FONT, color: COLORS.ink })],
          { x: x + 0.08, y, w: width - 0.1, h, align: 'left', valign: 'top', lineSpacingMultiple: 1.15, margin: 0 });
        man.entries.push({ kind: 'text', id: null });
        y += h + 0.08;
      }
      return y + 0.1;
    }
    case 'table': {
      const headRow = b.head ? [b.head.map(t => ({ text: String(t), options: { bold: true, color: COLORS.blue, fill: { color: COLORS.headBg } } }))] : [];
      const bodyRows = (b.rows || []).map(r => r.map(c => ({ text: String(c), options: { color: COLORS.ink, fill: { color: 'FFFFFF' } } })));
      const all = headRow.concat(bodyRows);
      const rowH = b.rowH || 0.46;
      slide.addTable(all, {
        x, y, w: width, rowH,
        fontSize: Math.round(15 * scale), fontFace: FONT,
        align: b.align || 'center', valign: 'middle',
        border: { type: 'solid', pt: 0.75, color: COLORS.line },
        autoPage: false,
        ...(Array.isArray(b.colW) && b.colW.length ? { colW: b.colW } : {}),
      });
      man.entries.push({ kind: 'table', id: null });
      return y + all.length * rowH + 0.25;
    }
    case 'code': {
      const lines = String(b.text).replace(/\n+$/, '').split('\n');
      const pt = b.size || 13.5;
      const per = pt >= 13 ? 0.30 : (pt <= 11 ? 0.23 : 0.25);
      const ch = Math.max(0.6, lines.length * per * scale + 0.35);
      slide.addShape('roundRect', { x: x + 0.02, y, w: width - 0.04, h: ch, rectRadius: 0.05, fill: { color: COLORS.codeBg }, line: { color: 'DDE4EF', width: 0.7 } });
      slide.addText(String(b.text), {
        x: x + 0.2, y: y + 0.12, w: width - 0.4, h: ch - 0.24,
        fontFace: CODE_FONT, fontSize: Math.round(pt * scale), color: COLORS.ink,
        align: 'left', valign: 'top', lineSpacingMultiple: 1.25, margin: 0,
      });
      man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null });
      return y + ch + 0.22;
    }
    case 'note': {
      const pt = Math.round((b.size || 15) * scale);
      const lines = estLines(b.text, pt, width);
      const h = lines * pt / 72 * 1.5 + 0.08;
      slide.addText(String(b.text), { x, y, w: width, h, fontSize: pt, fontFace: FONT, color: COLORS.gray, align: 'left', valign: 'top', margin: 0 });
      man.entries.push({ kind: 'text', id: null });
      return y + h + 0.12;
    }
    case 'text': {
      const pt = Math.round((b.size || 18) * scale);
      const lines = estLines(b.text, pt, width);
      const h = lines * pt / 72 * 1.5 + 0.08;
      slide.addText(parseRuns(b.text, { fontSize: pt, fontFace: FONT, color: b.color === 'blue' ? COLORS.blue : (b.color === 'red' ? COLORS.red : COLORS.ink), bold: !!b.bold }),
        { x, y, w: width, h, align: b.align || 'left', valign: 'top', margin: 0 });
      man.entries.push({ kind: 'text', id: null });
      return y + h + 0.14;
    }
    case 'gap': return y + (b.h || 0.2);
    case 'image': {
      const src = b.src || b.path;
      if (!src) return y + 0.4;
      const imgPath = path.isAbsolute(src) ? src : path.resolve(PROJECT_ROOT, src);
      if (!fs.existsSync(imgPath)) {
        overflowReport.push(`图片未找到: ${src}`);
        return y + 0.6;
      }
      const iw = Math.min(b.w || (width * 0.72), width);
      const ih = b.h || (iw * 0.66);
      const ix = b.align === 'center' ? (x + (width - iw) / 2) : x;
      slide.addImage({ path: imgPath, x: ix, y, w: iw, h: ih });
      man.entries.push({ kind: 'image', id: null });
      return y + ih + 0.2;
    }
    case 'diagram': return renderDiagram(pptx, slide, b, y, scale, man, x, width);
    default: return y + 0.4;
  }
}

// ===== diagram（v1 的 array/linkedlist 原生画法，视觉一致） =====
function renderDiagram(pptx, slide, b, y, scale, man, x0 = MX, width = CW) {
  const w = Math.min(b.w || (width * 0.8), width), h = b.h || 1.5;
  const x = b.align === 'center' ? (x0 + (width - w) / 2) : x0;
  if (b.diagram === 'array') {
    const cells = b.cells || [], n = cells.length;
    if (!n) return y;
    const cellW = w / n, cellH = h * 0.55, indexH = h * 0.18;
    for (let i = 0; i < n; i++) {
      const cx = x + i * cellW;
      const isHL = (b.highlight || []).includes(i);
      slide.addShape('rect', { x: cx, y, w: cellW, h: cellH, fill: { color: isHL ? COLORS.hlBg : 'FFFFFF' }, line: { color: isHL ? COLORS.red : COLORS.line, width: 1 } });
      slide.addText(String(cells[i]), { x: cx, y, w: cellW, h: cellH, fontSize: Math.round(14 * scale), fontFace: FONT, color: COLORS.ink, align: 'center', valign: 'middle', margin: 0 });
      if (b.indices !== false) slide.addText(String(i), { x: cx, y: y + cellH, w: cellW, h: indexH, fontSize: Math.round(10 * scale), fontFace: FONT, color: COLORS.gray, align: 'center', valign: 'top', margin: 0 });
      man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null }, { kind: 'text', id: null });
    }
    for (const ptr of (b.pointers || [])) {
      const idx = ptr.index !== undefined ? ptr.index : ptr.value;
      if (idx < 0 || idx >= n) continue;
      const px = x + idx * cellW + cellW / 2;
      const above = ptr.position === 'above';
      const ay = above ? y - 0.24 : y + cellH + (b.indices !== false ? indexH : 0) + 0.02;
      slide.addShape('line', { x: px, y: ay, w: 0, h: 0.22, line: { color: COLORS.blue, width: 1.5, endArrowType: 'triangle' }, flipV: above });
      slide.addText(ptr.label || '', { x: px - 0.6, y: above ? ay - 0.24 : ay + 0.22, w: 1.2, h: 0.24, fontSize: Math.round(10 * scale), fontFace: FONT, color: COLORS.blue, bold: true, align: 'center', valign: 'middle', margin: 0 });
      man.entries.push({ kind: 'shape', id: null, arrow: true }, { kind: 'text', id: null });
    }
    return y + h + 0.2;
  }
  if (b.diagram === 'linkedlist') {
    const nodes = b.nodes || [], n = nodes.length;
    if (!n) return y;
    const head = b.head !== false, headLabel = b.headLabel || '';
    const isDouble = b.double === true;
    const total = n + (head ? 1 : 0);
    const nodeW = w / total, nodeH = h * 0.6;
    const priorW = isDouble ? nodeW * 0.25 : 0, dataW = isDouble ? nodeW * 0.5 : nodeW * 0.62, nextW = isDouble ? nodeW * 0.25 : nodeW * 0.38;
    for (let i = 0; i < total; i++) {
      const nx = x + i * nodeW;
      const isHead = head && i === 0;
      const isFirst = i === 0, isLast = i === total - 1;
      const value = isHead ? headLabel : nodes[i - (head ? 1 : 0)];
      const circular = b.circular === true && isLast;
      slide.addShape('rect', { x: nx, y, w: nodeW, h: nodeH, fill: { color: isHead ? COLORS.headBg : 'FFFFFF' }, line: { color: COLORS.line, width: 1 } });
      man.entries.push({ kind: 'shape', id: null });
      if (isDouble) {
        slide.addShape('line', { x: nx + priorW, y, w: 0, h: nodeH, line: { color: COLORS.line, width: 1 } });
        slide.addShape('line', { x: nx + priorW + dataW, y, w: 0, h: nodeH, line: { color: COLORS.line, width: 1 } });
        slide.addText(isFirst && !circular ? '∧' : '←', { x: nx, y, w: priorW, h: nodeH, fontSize: Math.round(13 * scale), fontFace: FONT, color: isFirst && !circular ? COLORS.gray : COLORS.blue, align: 'center', valign: 'middle', margin: 0 });
        slide.addText(String(value), { x: nx + priorW, y, w: dataW, h: nodeH, fontSize: Math.round(13 * scale), fontFace: FONT, color: isHead ? COLORS.gray : COLORS.ink, align: 'center', valign: 'middle', margin: 0 });
        slide.addText(circular ? '↻' : (isLast && !b.circular ? '∧' : '→'), { x: nx + priorW + dataW, y, w: nextW, h: nodeH, fontSize: Math.round(13 * scale), fontFace: FONT, color: isLast && !b.circular ? COLORS.gray : COLORS.blue, align: 'center', valign: 'middle', margin: 0 });
        man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null }, { kind: 'text', id: null }, { kind: 'text', id: null });
      } else {
        slide.addShape('line', { x: nx + dataW, y, w: 0, h: nodeH, line: { color: COLORS.line, width: 1 } });
        slide.addText(String(value), { x: nx, y, w: dataW, h: nodeH, fontSize: Math.round(13 * scale), fontFace: FONT, color: isHead ? COLORS.gray : COLORS.ink, align: 'center', valign: 'middle', margin: 0 });
        slide.addText(circular ? '↻' : (isLast && !b.circular ? '∧' : '→'), { x: nx + dataW, y, w: nextW, h: nodeH, fontSize: Math.round(14 * scale), fontFace: FONT, color: isLast && !b.circular ? COLORS.gray : COLORS.blue, align: 'center', valign: 'middle', margin: 0 });
        man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null }, { kind: 'text', id: null });
      }
    }
    return y + h + 0.2;
  }
  return y + 0.2;
}

// ================= 页面骨架 =================
function baseSlide(pptx, pageNo, total, man) {
  const slide = pptx.addSlide();
  slide.background = { path: path.resolve(PROJECT_ROOT, '课程', '素材', '底图.jpg') };
  slide.addText(pageNo + ' / ' + total, { x: W - 2, y: FOOT_Y, w: 2 - MX + 0.5, h: 0.35, fontSize: 10, fontFace: FONT, color: COLORS.gray, align: 'right', margin: 0 });
  man.entries.push({ kind: 'text', id: null, name: `p${String(pageNo).padStart(2, '0')}:pageno` });
  return slide;
}
function renderHeader(slide, sl, man, pageNo) {
  if (sl.kicker) {
    slide.addText(sl.kicker, { x: MX, y: TOP, w: CW, h: 0.4, fontSize: 14, fontFace: FONT, color: COLORS.blue, bold: true, align: 'left', margin: 0 });
    man.entries.push({ kind: 'text', id: null, name: `p${String(pageNo).padStart(2, '0')}:kicker` });
  }
  if (sl.title) {
    slide.addText(sl.title, { x: MX, y: TOP + 0.42, w: CW, h: 0.8, fontSize: 28, fontFace: FONT, color: COLORS.ink, bold: true, align: 'left', margin: 0 });
    man.entries.push({ kind: 'text', id: null, name: `p${String(pageNo).padStart(2, '0')}:title` });
  }
}

// ================= 混合页 =================
function renderHybrid(pptx, deck, lessonId, sl, pageNo, total, spec, man) {
  const pn = String(pageNo).padStart(2, '0');
  const slide = baseSlide(pptx, pageNo, total, man);
  // 角标
  if (sl.badge) {
    slide.addShape('roundRect', { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fill: { color: 'FFFFFF' }, line: { color: COLORS.red, width: 1.2 }, rectRadius: 0.08 });
    slide.addText(sl.badge, { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fontSize: 13, fontFace: FONT, color: COLORS.red, bold: true, align: 'center', valign: 'middle', margin: 0 });
    man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null });
  }
  renderHeader(slide, sl, man, pageNo);

  const assetsDir = path.join(deck._lessonDir, 'assets');
  const asset = id => path.join(assetsDir, `${lessonId}-p${pn}-fixed-${id}.png`);
  const animAsset = id => path.join(assetsDir, `${lessonId}-p${pn}-${id}.png`);

  // 1) 固定层（PNG）
  for (const el of (spec.fixed || [])) {
    const f = asset(el.id);
    if (!fs.existsSync(f)) { overflowReport.push(`P${pageNo} 缺固定层素材 ${el.id}（先跑 shot.js）`); continue; }
    slide.addImage({ path: f, x: el.box[0], y: el.box[1], w: el.box[2], h: el.box[3] });
    man.entries.push({ kind: 'image', id: `p${pn}:${el.id}` });
    checkInContentArea(lessonId, pageNo, el.id, el.box, 'fixed');
  }
  // 2) 动画层（PNG，全部先加入；未出现在任何步骤且未标 always 的视为错误）
  const stepIds = new Set();
  for (const st of (spec.steps || [])) {
    for (const id of (st.appear || [])) stepIds.add(id);
    for (const id of (st.hide || [])) stepIds.add(id);
  }
  for (const el of (spec.anim || [])) {
    const f = animAsset(el.id);
    if (!fs.existsSync(f)) { overflowReport.push(`P${pageNo} 缺动画素材 ${el.id}（先跑 shot.js）`); continue; }
    if (!stepIds.has(el.id) && !el.always) overflowReport.push(`P${pageNo} 动画元素 ${el.id} 未出现在 steps 且未标 always`);
    slide.addImage({ path: f, x: el.box[0], y: el.box[1], w: el.box[2], h: el.box[3] });
    man.entries.push({ kind: 'image', id: `p${pn}:${el.id}` });
    checkInContentArea(lessonId, pageNo, el.id, el.box, 'anim');
  }
  // 3) 原生对象
  for (const el of (spec.native || [])) {
    addNative(pptx, slide, el, man, pn);
    if (el.box) {
      // line 元素的 box 语义是 [x1,y1,x2,y2]，检查时先归一化为 [x,y,w,h]
      const nb = el.kind === 'line'
        ? [Math.min(el.box[0], el.box[2]), Math.min(el.box[1], el.box[3]), Math.abs(el.box[2] - el.box[0]), Math.abs(el.box[3] - el.box[1])]
        : el.box;
      checkInContentArea(lessonId, pageNo, el.id, nb, 'native');
    }
  }
  // 步骤元素存在性校验
  const known = new Set();
  for (const el of (spec.fixed || [])) known.add(el.id);
  for (const el of (spec.anim || [])) known.add(el.id);
  for (const el of (spec.native || [])) known.add(el.id);
  for (const id of stepIds) if (!known.has(id)) overflowReport.push(`P${pageNo} steps 引用了未定义元素 ${id}`);
  // 动画页（含 anim 元素或声明了 steps）必须有 steps；纯静态混合页（仅 fixed/native）不需要
  if ((spec.anim || []).length && (!spec.steps || !spec.steps.length)) overflowReport.push(`P${pageNo} 动画页没有 steps`);
  // steps 里引用的元素若带 always 标记则矛盾
  for (const el of (spec.anim || [])) {
    if (el.always && stepIds.has(el.id)) overflowReport.push(`P${pageNo} ${el.id} 标了 always 又出现在 steps`);
  }
}

function addNative(pptx, slide, el, man, pn) {
  const p = el.props || {};
  const name = `p${pn}:${el.id}`;
  const [x, y, w, h] = el.box || [0, 0, 1, 1];
  switch (el.kind) {
    case 'bullets': {
      // items 数组在一个文本框里逐条出现（bullet 样式与原生页一致）
      const pt = p.fontSize || 16;
      const items = p.items || [];
      const runs = [];
      items.forEach((it, i) => {
        runs.push({ text: '•  ', options: { fontSize: pt, fontFace: FONT, color: COLORS.blue, bold: true, breakLine: false } });
        const arr = parseRuns(it, { fontSize: pt, fontFace: FONT, color: p.color || COLORS.ink, bold: !!p.bold });
        runs.push(...arr.map(r => ({ text: r.text, options: Object.assign({ breakLine: false }, r.options || {}) })));
        runs[runs.length - 1].options.breakLine = true;
      });
      // 行高校验
      let need = 0;
      for (const it of items) need += estLines(it, pt, w - 0.3) * pt / 72 * 1.35 + 0.06;
      if (need > h + 0.05) overflowReport.push(`[bullets ${name}] 文本需 ${need.toFixed(2)}in > 框高 ${h}in`);
      slide.addText(runs, { x, y, w, h, align: p.align || 'left', valign: p.valign || 'top', fontSize: pt, fontFace: FONT, color: p.color || COLORS.ink, lineSpacingMultiple: p.lineSpacing || 1.15, paraSpaceAfter: p.paraSpaceAfter != null ? p.paraSpaceAfter : 6, margin: 0 });
      man.entries.push({ kind: 'text', id: name });
      break;
    }
    case 'code': {
      const pt = p.fontSize || 12;
      const code = String(p.text || '');
      const lines = code.replace(/\n+$/, '').split('\n');
      const maxWidth = Math.max(0, ...lines.map(line => line.length * pt * 0.60 / 72));
      const needH = lines.length * pt * 1.35 / 72 + 0.28;
      if (maxWidth > w - 0.32) overflowReport.push(`[code ${name}] 单行代码估算 ${maxWidth.toFixed(2)}in > 框宽 ${Math.max(0,w-0.32).toFixed(2)}in`);
      if (needH > h + 0.05) overflowReport.push(`[code ${name}] 代码需 ${needH.toFixed(2)}in > 框高 ${h}in`);
      slide.addShape('roundRect', { x, y, w, h, rectRadius: 0.05, fill: { color: COLORS.codeBg }, line: { color: 'DDE4EF', width: 0.7 } });
      slide.addText(code, { x: x + 0.16, y: y + 0.12, w: w - 0.32, h: h - 0.24, fontSize: pt, fontFace: p.fontFace || CODE_FONT, color: p.color || COLORS.ink, align: 'left', valign: 'top', lineSpacingMultiple: 1.25, margin: 0 });
      man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null });
      break;
    }
    case 'text': case 'note': {
      const pt = p.fontSize || (el.kind === 'note' ? 14 : 16);
      const color = p.color || (el.kind === 'note' ? COLORS.gray : COLORS.ink);
      const need = estTextHeight(p.text || '', pt, w, 1.4);
      if (need > h + 0.05) overflowReport.push(`[text ${name}] 文本需 ${need.toFixed(2)}in > 框高 ${h}in（估行数 estLines）`);
      slide.addText(parseRuns(p.text || '', { fontSize: pt, fontFace: FONT, color, bold: !!p.bold }),
        { x, y, w, h, align: p.align || 'left', valign: p.valign || 'top', fontSize: pt, fontFace: p.fontFace || FONT, color, bold: !!p.bold, lineSpacingMultiple: p.lineSpacing || 1.2, margin: 0 });
      man.entries.push({ kind: 'text', id: name });
      break;
    }
    case 'rect': {
      slide.addShape(p.rounded ? 'roundRect' : 'rect', {
        x, y, w, h,
        fill: p.fill ? { color: p.fill, transparency: p.transparency != null ? p.transparency : 0 } : { color: 'FFFFFF', transparency: 100 },
        line: p.lineColor ? { color: p.lineColor, width: p.lineW || 1.5, dashType: p.dash || 'solid' } : { type: 'none' },
        ...(p.rounded ? { rectRadius: 0.06 } : {}),
      });
      man.entries.push({ kind: 'shape', id: name });
      break;
    }
    case 'oval': {
      slide.addShape('ellipse', {
        x, y, w, h,
        fill: p.fill ? { color: p.fill, transparency: p.transparency != null ? p.transparency : 0 } : { color: 'FFFFFF', transparency: 100 },
        line: p.lineColor ? { color: p.lineColor, width: p.lineW || 2 } : { type: 'none' },
      });
      man.entries.push({ kind: 'shape', id: name });
      break;
    }
    case 'line': {
      // box 语义: [x1,y1,x2,y2]（允许任意方向）
      const [x1, y1, x2, y2] = el.box;
      const bx = Math.min(x1, x2), by = Math.min(y1, y2);
      const bw = Math.abs(x2 - x1), bh = Math.abs(y2 - y1);
      const o = {
        x: bx, y: by, w: bw, h: bh,
        line: { color: p.color || COLORS.blue, width: p.width || 2, dashType: p.dash || 'solid' },
      };
      if (p.arrow === 'end' || p.arrow === 'both' || p.arrow == null) o.line.endArrowType = p.head || 'triangle';
      if (p.arrow === 'both') o.line.beginArrowType = p.head || 'triangle';
      if (p.arrow === 'none') { delete o.line.endArrowType; }
      if (x2 < x1) o.flipH = true;
      if (y2 < y1) o.flipV = true;
      slide.addShape('line', o);
      man.entries.push({ kind: 'shape', id: name, arrow: o.line.endArrowType || o.line.beginArrowType ? true : false });
      break;
    }
    default: throw new Error('未知 native kind: ' + el.kind);
  }
}

// ================= 原生页 =================
function renderNativePage(pptx, deck, lessonId, sl, pageNo, total, man) {
  const slide = baseSlide(pptx, pageNo, total, man);
  if (sl.badge) {
    slide.addShape('roundRect', { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fill: { color: 'FFFFFF' }, line: { color: COLORS.red, width: 1.2 }, rectRadius: 0.08 });
    slide.addText(sl.badge, { x: W - MX - 2.5, y: TOP, w: 2.5, h: 0.5, fontSize: 13, fontFace: FONT, color: COLORS.red, bold: true, align: 'center', valign: 'middle', margin: 0 });
    man.entries.push({ kind: 'shape', id: null }, { kind: 'text', id: null });
  }
  renderHeader(slide, sl, man, pageNo);
  if (sl.layout === 'split' && Array.isArray(sl.columns)) {
    renderSplitColumns(pptx, slide, lessonId, sl, pageNo, man);
    return slide;
  }
  let y = BODY_TOP;
  const avail = CONTENT_BOTTOM - y;
  let need = 0;
  const nativeBlocks = sl.blocks || [];
  for (const b of nativeBlocks) {
    const h = blockHeight(b, CW);
    if (!Number.isFinite(h) || h < 0) {
      reportOverflow(lessonId, pageNo, '内容规格无效', `${b.type || 'unknown'} 块无法估算高度`);
      continue;
    }
    need += h;
  }
  if (nativeBlocks.length) need = Math.max(0, need - blockTail(nativeBlocks[nativeBlocks.length - 1]));
  const scale = need > avail ? Math.max(0.5, avail / need) : 1;
  if (need > avail) {
    // 不静默缩了事：缩放后仍溢出或缩放低于 0.9 都记为构建错误
    const scaledNeed = need * scale;
    if (scale < 0.9 || scaledNeed > avail + 0.05) {
      reportOverflow(lessonId, pageNo, '内容超容量', `需 ${need.toFixed(2)}in / 可用 ${avail.toFixed(2)}in（scale=${scale.toFixed(2)}）——拆页或精简`);
    }
  }
  for (const b of nativeBlocks) { y = renderBlock(pptx, slide, b, y, scale, man); if (process.env.DEBUG_Y) console.log("debug P"+pageNo, b.type, "end y="+y.toFixed(2)); }
  if (nativeBlocks.length) y -= blockTail(nativeBlocks[nativeBlocks.length - 1]);
  if (y > CONTENT_BOTTOM + 0.06) {
    reportOverflow(lessonId, pageNo, '内容底部越界', `结束于 y=${y.toFixed(2)}in > ${CONTENT_BOTTOM}in`);
  }
}

function renderSplitColumns(pptx, slide, lessonId, sl, pageNo, man) {
  const gap = 0.28;
  const leftW = sl.leftWidth || 7.25;
  const rightW = CW - leftW - gap;
  const cols = [
    { x: MX, w: leftW, blocks: sl.columns[0] || [], label: sl.columnLabels && sl.columnLabels[0] },
    { x: MX + leftW + gap, w: rightW, blocks: sl.columns[1] || [], label: sl.columnLabels && sl.columnLabels[1] },
  ];
  const avail = CONTENT_BOTTOM - BODY_TOP;
  for (const col of cols) {
    let y = BODY_TOP;
    if (col.label) {
      slide.addText(col.label, { x: col.x, y: BODY_TOP, w: col.w, h: 0.28, fontSize: 11, fontFace: FONT, color: COLORS.blue, bold: true, align: 'left', margin: 0 });
      man.entries.push({ kind: 'text', id: null });
      y += 0.34;
    }
    let need = 0;
    for (const b of col.blocks) {
      const h = blockHeight(b, col.w);
      if (!Number.isFinite(h) || h < 0) {
        reportOverflow(lessonId, pageNo, '分栏内容规格无效', `${b.type || 'unknown'} 块无法估算高度`);
        continue;
      }
      need += h;
    }
    if (col.blocks.length) need = Math.max(0, need - blockTail(col.blocks[col.blocks.length - 1]));
    const columnAvail = CONTENT_BOTTOM - y;
    const scale = need > columnAvail ? Math.max(0.5, columnAvail / need) : 1;
    if (need > columnAvail && (scale < 0.9 || need * scale > columnAvail + 0.05)) {
      reportOverflow(lessonId, pageNo, '分栏内容超容量', `需 ${need.toFixed(2)}in / 可用 ${columnAvail.toFixed(2)}in（scale=${scale.toFixed(2)}）——拆页或精简`);
    }
    for (const b of col.blocks) y = renderBlock(pptx, slide, b, y, scale, man, col.x, col.w);
    if (col.blocks.length) y -= blockTail(col.blocks[col.blocks.length - 1]);
    if (y > CONTENT_BOTTOM + 0.06) reportOverflow(lessonId, pageNo, '分栏底部越界', `结束于 y=${y.toFixed(2)}in > ${CONTENT_BOTTOM}in`);
  }
}

function renderCover(pptx, deck, sl, pageNo, total, man) {
  const slide = baseSlide(pptx, pageNo, total, man);
  const cy = 2.35;
  if (sl.kicker) { slide.addText(sl.kicker, { x: 0, y: cy, w: W, h: 0.5, fontSize: 18, fontFace: FONT, color: COLORS.blue, bold: true, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null }); }
  slide.addText(sl.title || '', { x: 0, y: cy + 0.75, w: W, h: 1.25, fontSize: 48, fontFace: FONT, color: COLORS.ink, bold: true, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null });
  if (sl.subtitle) { slide.addText(sl.subtitle, { x: 0, y: cy + 2.15, w: W, h: 0.6, fontSize: 20, fontFace: FONT, color: COLORS.ink, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null }); }
  if (sl.meta) { slide.addText(sl.meta, { x: 0, y: cy + 2.95, w: W, h: 0.5, fontSize: 14, fontFace: FONT, color: COLORS.gray, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null }); }
}
function renderTransition(pptx, deck, sl, pageNo, total, man) {
  const slide = baseSlide(pptx, pageNo, total, man);
  const cy = 3.0;
  if (sl.kicker) { slide.addText(sl.kicker, { x: 0, y: cy - 0.75, w: W, h: 0.45, fontSize: 16, fontFace: FONT, color: COLORS.blue, bold: true, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null }); }
  slide.addText(sl.title || '', { x: 0, y: cy, w: W, h: 0.95, fontSize: 38, fontFace: FONT, color: COLORS.ink, bold: true, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null });
  if (sl.subtitle) { slide.addText(sl.subtitle, { x: 0, y: cy + 1.05, w: W, h: 0.55, fontSize: 17, fontFace: FONT, color: COLORS.gray, align: 'center', margin: 0 }); man.entries.push({ kind: 'text', id: null }); }
}

// ================= 主流程 =================
async function main() {
  if (!process.argv[2]) throw new Error('用法: node render-v2.js <优化版课节目录>');
  const lessonDir = assertOptimizedLessonDir(process.argv[2]);
  const lessonId = path.basename(lessonDir);
  const deck = yaml.load(fs.readFileSync(path.join(lessonDir, 'deck.yaml'), 'utf8'));
  if (!deck || !Array.isArray(deck.slides) || deck.slides.length === 0) throw new Error('deck.yaml 必须包含非空 slides 数组');
  if (deck.meta && deck.meta.id && deck.meta.id !== lessonId) throw new Error(`meta.id ${deck.meta.id} 与目录 ${lessonId} 不一致`);
  deck._lessonDir = lessonDir;
  const slides = deck.slides || [];
  const pagesDir = path.join(lessonDir, 'pages');
  const specs = {};
  if (fs.existsSync(pagesDir)) {
    for (const f of fs.readdirSync(pagesDir).filter(f => /^p\d+\.yaml$/.test(f)).sort()) {
      const s = yaml.load(fs.readFileSync(path.join(pagesDir, f), 'utf8'));
      const filenamePage = Number(f.match(/^p(\d+)\.yaml$/)[1]);
      if (!s || !Number.isInteger(s.page) || s.page !== filenamePage || s.page < 1 || s.page > slides.length) {
        throw new Error(`${f}: page 必须与文件名一致，并位于 1..${slides.length}`);
      }
      if (Object.prototype.hasOwnProperty.call(specs, s.page)) throw new Error(`P${s.page} 有重复 pages 规格`);
      specs[s.page] = s;
    }
  }
  const outPath = path.join(lessonDir, `${lessonId}.pptx`);

  const pptx = new PptxGenJS();
  pptx.defineLayout({ name: 'W16x9', width: W, height: H });
  pptx.layout = 'W16x9';
  pptx.author = (deck.meta && deck.meta.instructor) || '';
  pptx.title = (deck.meta && deck.meta.title) || '';

  const manifest = { lesson: lessonId, slides: [] };
  slides.forEach((sl, i) => {
    const pageNo = i + 1, total = slides.length;
    const man = { page: pageNo, entries: [] };
    manifest.slides.push(man);
    const spec = specs[pageNo];
    if (spec && (spec.fixed || spec.anim || spec.native)) {
      renderHybrid(pptx, deck, lessonId, sl, pageNo, total, spec, man);
    } else {
      switch (sl.type) {
        case 'cover': return renderCover(pptx, deck, sl, pageNo, total, man);
        case 'transition': return renderTransition(pptx, deck, sl, pageNo, total, man);
        default: return renderNativePage(pptx, deck, lessonId, sl, pageNo, total, man);
      }
    }
  });

  if (overflowReport.length) {
    console.error(`\n===== 构建中止：溢出/规格错误 ${overflowReport.length} 项，未写入产物 =====`);
    overflowReport.forEach(r => console.error('  [溢出] ' + r));
    throw new Error('请先处理以上问题，再重新构建。');
  }

  const manifestPath = path.join(lessonDir, 'manifest.json');
  // pptxgenjs 会为不含 .pptx 后缀的 fileName 自动补扩展名；让临时路径本身以 .pptx 结尾，
  // 否则文件实际写成 .tmp.pptx，后续原子替换会找不到预期路径。
  const tempPptx = `${outPath}.${process.pid}.tmp.pptx`;
  const tempManifest = `${manifestPath}.${process.pid}.tmp`;
  try {
    await pptx.writeFile({ fileName: tempPptx });
    fs.writeFileSync(tempManifest, JSON.stringify(manifest, null, 1), 'utf8');
    fs.renameSync(tempPptx, outPath);
    fs.renameSync(tempManifest, manifestPath);
  } finally {
    for (const file of [tempPptx, tempManifest]) {
      if (fs.existsSync(file)) fs.rmSync(file, { force: true });
    }
  }

  const hybridCount = Object.keys(specs).length;
  console.log(`OK -> ${outPath} (${slides.length} 页, 混合动画页 ${hybridCount})`);
}
main().catch(e => { console.error(e); process.exit(1); });
