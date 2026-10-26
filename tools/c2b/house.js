// house.js —— C2-B 优化版共享常量与 HTML 组件库
// 坐标唯一来源：本文件定义画布常量，HTML 渲染（192px/in）与 PPT（英寸）都从这里取数。
'use strict';
const path = require('path');

// ===== 画布与安全区（与 tools/render-pptx.js 同一套，不可改机构底图区域） =====
const CANVAS = {
  W: 13.333, H: 7.5,          // 16:9 英寸
  MX: 0.9,                    // 左右边距
  TOP: 1.05,                  // 顶部安全区（避开底图顶部机构色带）
  BODY_TOP: 2.62,             // 正文起始
  FOOT_Y: 6.58,               // 页脚
  CONTENT_BOTTOM: 6.42,       // 内容块底边界（底图底部广告条约 7.10in 起）
};
const PPI = 192;              // HTML 渲染分辨率：192px/in（2560×1440）
const COLORS = {
  ink: '1F2329', blue: '1F4E9C', red: 'C0392B', gray: '8A9099',
  line: 'D8DBE0', headBg: 'F5F6F7', codeBg: 'F7F9FC',
  hlBg: 'FFF3CD', tintBlue: 'E8EEF9',
};
const FONT_CJK = "'Microsoft YaHei','微软雅黑',sans-serif";
const FONT_CODE = "Consolas,'Courier New',monospace";

function inch2px(v) { return Math.round(v * PPI); }
function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ===== 文本行数估算（CJK 全宽、ASCII 0.55 宽，比 v1 更保守） =====
function weightedLen(s) {
  let n = 0;
  for (const ch of String(s)) n += ch.charCodeAt(0) > 0x2e80 ? 1 : 0.55;
  return n;
}
function estLines(text, pt, widthIn) {
  const per = Math.max(1, widthIn / (pt / 72));
  let n = 0;
  for (const seg of String(text).split('\n')) n += Math.max(1, Math.ceil(weightedLen(seg) / per));
  return n;
}
// native 文本块估算高度（英寸），与 v1 行距策略一致
function estTextHeight(text, pt, widthIn, lineSpacing = 1.5) {
  return estLines(text, pt, widthIn) * pt / 72 * lineSpacing;
}

// ===== 代码语法高亮（静态烘焙；关键词蓝、注释灰，遵守三色制） =====
const C_KEYWORDS = /\b(void|int|bool|char|struct|for|while|if|else|return|typedef|const|break|continue|sizeof|true|false|NULL|INF)\b/g;
function highlightCode(line) {
  let out = esc(line);
  // 注释：第一个 // 之后整段灰
  const ci = out.indexOf('//');
  let code = out, comment = '';
  if (ci >= 0) { code = out.slice(0, ci); comment = '<span style="color:#8A9099">' + out.slice(ci) + '</span>'; }
  code = code.replace(C_KEYWORDS, '<span style="color:#1F4E9C;font-weight:600">$1</span>');
  return code + comment;
}

// ===== 组件：返回绝对定位 HTML 片段（坐标系 = 元素 box 左上角） =====
// 每个组件独立可替换：一个元素 = 一个命名 PNG。
const Comps = {
  // 代码面板：浅底 + 左蓝竖条（沿用 v1 代码块识别符）
  // props: {text, fontSizePx(@192ppi, 32≈12pt), lineHeight, focus:[行号1-based], slice:[起,止]}
  code(el) {
    const p = el.props || {};
    const fs = p.fontSizePx || 32;               // 32px@192ppi = 12pt
    const lh = p.lineHeight || 1.55;
    let lines = String(p.text).replace(/\t/g, '    ').split('\n');
    if (p.slice) lines = lines.slice(p.slice[0] - 1, p.slice[1]);
    const rows = lines.map((ln, i) => {
      const cls = (p.focus || []).includes(i + 1) ? ' cfocus' : '';
      return `<div class="cl${cls}">${highlightCode(ln) || '&nbsp;'}</div>`;
    });
    return `<div class="el codepanel" style="left:0;top:0;width:100%;height:100%">
      <div class="codebar"></div><div class="coderows" style="font-size:${fs}px;line-height:${lh}">${rows.join('')}</div></div>`;
  },
  // 链表结点壳（数据域+指针域；结点间箭头由 PPT 原生线条承担）
  // props: {head:'L', nodes:[...], double, nodeW, nodeH, gapPx, labelPx, top}
  // 产出 el._geometry = [{cx, left, right, top, bottom, isHead}, ...]（inch，供页面作者换算原生线条端点）
  linked(el) {
    const p = el.props || {};
    const nodes = p.nodes || [];
    const headLabel = p.head || '';
    const double = !!p.double;
    const n = nodes.length + (headLabel ? 1 : 0);
    const gap = p.gapPx != null ? p.gapPx : 26;
    const unit = p.nodeW || 110;                 // 每结点总宽 px
    const h = p.nodeH || 64;
    const top = p.top || 0;
    const dataW = double ? unit * 0.5 : unit * 0.64;
    let x = 0, html = '';
    el._geometry = [];
    for (let i = 0; i < n; i++) {
      const isHead = headLabel && i === 0;
      const label = isHead ? headLabel : nodes[i - (headLabel ? 1 : 0)];
      const border = isHead ? '#8A9099' : '#1F4E9C';
      const fill = isHead ? '#F5F6F7' : '#FFFFFF';
      const textColor = isHead ? '#8A9099' : '#1F2329';
      html += `<div class="lnode" style="left:${x}px;top:${top}px;width:${unit}px;height:${h}px;border:3px solid ${border};background:${fill}">`;
      if (double) {
        const pw = unit * 0.25;
        html += `<div class="lnode-cell" style="width:${pw}px;color:#1F4E9C">${isHead ? '∧' : '←'}</div>`
          + `<div class="lnode-cell" style="width:${dataW - pw}px;color:${textColor};font-weight:600">${esc(label)}</div>`
          + `<div class="lnode-cell" style="width:${pw}px;color:#1F4E9C">→</div>`;
      } else {
        html += `<div class="lnode-cell" style="width:${dataW}px;color:${textColor};font-weight:600">${esc(label)}</div>`
          + `<div class="lnode-cell" style="width:${unit - dataW}px;color:#1F4E9C">→</div>`;
      }
      html += `</div>`;
      if (isHead) html += `<div class="lhead-tag" style="left:${x + (unit - 120) / 2}px;top:${top + h + 6}px;width:120px">头结点</div>`;
      el._geometry.push({ px: { x, w: unit, h, top, cx: x + unit / 2, cy: top + h / 2, right: x + unit, bottom: top + h }, isHead, label });
      x += unit + gap;
    }
    return wrap(html);
  },
  // 通用结点方块（数组/队列格子壳）
  cells(el) {
    const p = el.props || {};
    const vals = p.cells || [];
    const cw = p.cellW || 84, ch = p.cellH || 64;
    const idx = p.indices !== false;
    let html = '';
    vals.forEach((v, i) => {
      const x = i * (cw + (p.gapPx || 0));
      html += `<div class="cellbox" style="left:${x}px;top:0;width:${cw}px;height:${ch}px"><span>${esc(v)}</span></div>`;
      if (idx) html += `<div class="cellidx" style="left:${x}px;top:${ch + 4}px;width:${cw}px">${p.indexFrom !== undefined ? p.indexFrom + i : i}</div>`;
    });
    return wrap(html);
  },
  // 网格壳（位图/矩阵），值与染色由 PPT 原生对象承担
  grid(el) {
    const p = el.props || {};
    const rows = p.rows, cols = p.cols;
    const cw = p.cellW || 96, ch = p.cellH || 96;
    const gap = p.gapPx || 6;
    let html = '';
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = (p.labelW || 40) + c * (cw + gap), y = (p.labelH || 34) + r * (ch + gap);
      html += `<div class="gridcell" style="left:${x}px;top:${y}px;width:${cw}px;height:${ch}px"></div>`;
    }
    if (p.colLabels) p.colLabels.forEach((t, c) => {
      html += `<div class="gridlab" style="left:${(p.labelW || 40) + c * (cw + gap)}px;top:0;width:${cw}px;height:${p.labelH || 34}px">${esc(t)}</div>`;
    });
    if (p.rowLabels) p.rowLabels.forEach((t, r) => {
      html += `<div class="gridlab" style="left:0;top:${(p.labelH || 34) + r * (ch + gap)}px;width:${p.labelW || 40}px;height:${ch}px">${esc(t)}</div>`;
    });
    return wrap(html);
  },
  // 圆结点（树）；位置由 props.nodes:[[cx,cy,label?]] 提供，label 留空时 PPT 原生文字承担
  treeNodes(el) {
    const p = el.props || {};
    const r = p.r || 42;
    let html = '';
    for (const nd of (p.nodes || [])) {
      const [cx, cy, label] = nd;
      html += `<div class="tnode" style="left:${cx - r}px;top:${cy - r}px;width:${r * 2}px;height:${r * 2}px;${p.hollow ? 'background:#fff' : ''}">${label !== undefined && label !== null && label !== '' ? `<span>${esc(label)}</span>` : ''}</div>`;
    }
    // 边（可选静态）
    for (const e of (p.edges || [])) {
      const [a, b] = e;
      const na = p.nodes[a], nb = p.nodes[b];
      html += svgEdge(na[0], na[1], nb[0], nb[1], r, '#1F2329', 3, false);
    }
    return wrap(html);
  },
  // 面板容器（浅底、圆角、可选小标题）
  panel(el) {
    const p = el.props || {};
    return `<div class="el panel" style="left:0;top:0;width:100%;height:100%;background:${p.tint || '#F7F9FC'};border:1px solid ${p.border || '#D8DBE0'}">
      ${p.title ? `<div class="panel-title" style="color:${p.titleColor || '#1F4E9C'}">${esc(p.title)}</div>` : ''}</div>`;
  },
  // 箭头（PNG 动画对象，用于不便用原生线条的曲线/标注箭头）
  arrow(el) {
    const p = el.props || {};
    const w = el._boxPx[0], h = el._boxPx[1];
    const x1 = p.x1 != null ? p.x1 : 0, y1 = p.y1 != null ? p.y1 : h / 2;
    const x2 = p.x2 != null ? p.x2 : w, y2 = p.y2 != null ? p.y2 : h / 2;
    const color = '#' + (p.color || COLORS.blue);
    const wdt = p.width || 4;
    let html = `<svg width="${w}" height="${h}" style="position:absolute;left:0;top:0;overflow:visible">
      <defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 z" fill="${color}"/></marker></defs>
      <line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${wdt}" ${p.dash ? 'stroke-dasharray="10,7"' : ''} marker-end="url(#ah)"/></svg>`;
    if (p.label) html += `<div class="arrowsym" style="left:${(x1 + x2) / 2 - 60}px;top:${(y1 + y2) / 2 - 18}px;width:120px;color:${color}">${esc(p.label)}</div>`;
    return wrap(html);
  },
  // 小标签 chip（p/temp/dist 等指针名牌，PNG 动画对象）
  chip(el) {
    const p = el.props || {};
    return `<div class="el chip" style="left:0;top:0;width:100%;height:100%;background:#1F4E9C;color:#fff;font-size:${p.fontSizePx || 26}px;${p.hollow ? 'background:#fff;color:#1F4E9C;border:3px solid #1F4E9C;' : ''}">${esc(p.text || '')}</div>`;
  },
  // 图例行
  legend(el) {
    const p = el.props || {};
    return wrap((p.items || []).map(it =>
      `<div class="legend-item" style="font-size:${p.fontSizePx || 22}px">${it.swatch ? `<span class="sw" style="background:${it.swatch}"></span>` : ''}${esc(it.text)}</div>`).join(''));
  },
  // 静态图（沿用既有 assets/diagrams PNG 的包装，可与其他固定元素同层）
  image(el) {
    const p = el.props || {};
    const src = p.srcAbs; // 由调用方解析为绝对路径 file:// URL
    return `<img class="el" style="left:0;top:0;max-width:100%;max-height:100%;object-fit:contain" src="${src}">`;
  },
  // 自由 HTML（页面作者直接给片段，坐标相对 box）
  raw(el) {
    return `<div class="el" style="left:0;top:0;width:100%;height:100%">${el.props.html}</div>`;
  },
  // 带权图：nodes=[[cx,cy,label]](px)，edges=[[i,j,w]]，nodeR；edges 可选（灰底边）
  graph(el) {
    const p = el.props || {};
    const r = p.nodeR || 34;
    const nodes = p.nodes || [];
    let html = '';
    for (const e of (p.edges || [])) {
      const [a, b, w, dx, dy] = e;
      const na = nodes[a], nb = nodes[b];
      const dx0 = nb[0] - na[0], dy0 = nb[1] - na[1], L = Math.hypot(dx0, dy0) || 1;
      const ax = na[0] + dx0 / L * (r + 4), ay = na[1] + dy0 / L * (r + 4);
      const bx = nb[0] - dx0 / L * (r + 4), by = nb[1] - dy0 / L * (r + 4);
      html += `<svg style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible"><line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="#1F2329" stroke-width="3"/></svg>`;
      if (w !== undefined && w !== null) {
        const mx = (na[0] + nb[0]) / 2 + (dx || 0), my = (na[1] + nb[1]) / 2 + (dy || 0);
        html += `<div class="wlabel" style="left:${mx - 30}px;top:${my - 20}px;width:60px">${esc(w)}</div>`;
      }
    }
    for (const nd of nodes) {
      const [cx, cy, label] = nd;
      html += `<div class="tnode" style="left:${cx - r}px;top:${cy - r}px;width:${r * 2}px;height:${r * 2}px"><span>${esc(label)}</span></div>`;
    }
    return wrap(html);
  },
  // 双栏代码（props.text 的行按比例分列；或 props.cols=[lines1,lines2] 显式分列）
  code2col(el) {
    const p = el.props || {};
    const fs = p.fontSizePx || 24, lh = p.lineHeight || 1.55;
    let cols;
    if (p.cols) cols = p.cols.map(c => String(c).replace(/\t/g, '    ').split('\n'));
    else {
      const lines = String(p.text).replace(/\t/g, '    ').split('\n');
      const n = Math.ceil(lines.length / (p.nCols || 2));
      cols = [];
      for (let i = 0; i < lines.length; i += n) cols.push(lines.slice(i, i + n));
    }
    const colW = 100 / cols.length;
    return wrap(cols.map((lines, ci) =>
      `<div class="codepanel" style="position:absolute;left:${ci * colW}%;top:0;width:calc(${colW}% - 12px);height:100%">
        <div class="codebar"></div><div class="coderows" style="font-size:${fs}px;line-height:${lh}">${
        lines.map(ln => `<div class="cl">${highlightCode(ln) || '&nbsp;'}</div>`).join('')}</div></div>`).join(''));
  },
};

function wrap(inner) { return `<div class="el" style="left:0;top:0;width:100%;height:100%;position:absolute">${inner}</div>`; }
function svgEdge(x1, y1, x2, y2, r, color, wdt, dash) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
  const ux = dx / L, uy = dy / L;
  const ax = x1 + ux * (r + 3), ay = y1 + uy * (r + 3);
  const bx = x2 - ux * (r + 3), by = y2 - uy * (r + 3);
  return `<svg style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible"><line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="${color}" stroke-width="${wdt}" ${dash ? 'stroke-dasharray="10,7"' : ''}/></svg>`;
}

// ===== HTML 文档（截图用） =====
function elementDoc(el, boxPx, opts = {}) {
  // el: {id, component, props}; boxPx: [wpx, hpx]
  const comp = Comps[el.component];
  if (!comp) throw new Error('未知组件: ' + el.component);
  el._boxPx = boxPx;
  const inner = comp(el);
  const audit = opts.audit !== false ? auditScript() : '';
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:${boxPx[0]}px;height:${boxPx[1]}px;background:transparent;position:relative;overflow:visible;font-family:${FONT_CJK}}
.el{position:absolute}
.codepanel{background:${COLORS.codeBg};border-radius:2px}
.codebar{position:absolute;left:0;top:0;width:11px;height:100%;background:${COLORS.blue}}
.coderows{position:absolute;left:26px;top:14px;right:10px;bottom:10px;font-family:${FONT_CODE};color:${COLORS.ink};white-space:pre}
.cl{min-height:1em}
.cfocus{background:${COLORS.hlBg};box-shadow:0 0 0 2px ${COLORS.hlBg}}
.lnode{display:flex;position:absolute;border-radius:3px;overflow:hidden}
.lnode-cell{display:flex;align-items:center;justify-content:center;height:100%;font-size:${(el.props && el.props.labelPx) || 34}px;font-family:${FONT_CJK};border-right:2px solid #D8DBE0}
.lnode-cell:last-child{border-right:none}
.lhead-tag{position:absolute;font-size:20px;color:#8A9099;text-align:center}
.cellbox{position:absolute;border:3px solid #1F4E9C;background:#fff;display:flex;align-items:center;justify-content:center;font-size:${(el.props && el.props.labelPx) || 30}px;color:${COLORS.ink}}
.cellidx{position:absolute;text-align:center;font-size:22px;color:#8A9099}
.gridcell{position:absolute;border:3px solid #1F4E9C;background:#fff}
.gridlab{position:absolute;display:flex;align-items:center;justify-content:center;font-size:24px;color:#8A9099}
.tnode{position:absolute;border:3px solid #1F4E9C;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-size:${(el.props && el.props.labelPx) || 30}px;color:${COLORS.ink};font-weight:600}
.panel{border-radius:6px}
.panel-title{position:absolute;left:18px;top:10px;font-size:24px;font-weight:700}
.chip{display:flex;align-items:center;justify-content:center;border-radius:6px;font-weight:700;font-family:${FONT_CJK}}
.wlabel{position:absolute;text-align:center;font-size:30px;font-weight:700;color:#1F4E9C;font-family:${FONT_CJK}}
.legend-item{position:relative;display:flex;align-items:center;gap:10px;color:${COLORS.ink}}
.sw{display:inline-block;width:26px;height:26px;border:2px solid #1F4E9C}
.arrowsym{position:absolute;text-align:center;font-size:24px;font-weight:700;font-family:${FONT_CJK}}
</style></head><body>${inner}${audit}</body></html>`;
}

// 自检脚本：检查每个元素 box 内是否溢出，把结果写进 <title id="audit">
function auditScript() {
  return `<script>
window.addEventListener('load',()=>{
  const out=[];
  if(document.body.scrollWidth>document.body.clientWidth+1) out.push('body-w:'+document.body.scrollWidth+'>'+document.body.clientWidth);
  if(document.body.scrollHeight>document.body.clientHeight+1) out.push('body-h:'+document.body.scrollHeight+'>'+document.body.clientHeight);
  document.title='AUDIT|'+(out.length?out.join(';'):'OK');
  const t=document.createElement('div');t.id='audit-result';t.textContent='AUDIT|'+(out.length?out.join(';'):'OK');t.style.display='none';
  document.body.appendChild(t);
});
</script>`;
}

module.exports = { CANVAS, PPI, COLORS, FONT_CJK, FONT_CODE, Comps, elementDoc, estLines, estTextHeight, weightedLen, inch2px, esc };
