// 模拟 render-pptx.js 的高度计算，检查每页内容是否溢出
const fs = require('fs');
const yaml = require('js-yaml');

const CW = 13.333 - 0.9 * 2;
const BODY_TOP = 2.62, CONTENT_BOTTOM = 6.42;

function textLen(t) { return String(t).replace(/\*\*/g, '').length; }
function estLines(text, pt, width) {
  const cw = (pt / 72) * 1.06;
  const per = Math.max(1, Math.floor(width / cw));
  let n = 0;
  for (const seg of String(text).split('\n')) n += Math.max(1, Math.ceil(textLen(seg) / per));
  return n;
}
function blockHeight(b) {
  switch (b.type) {
    case 'bullets': {
      let n = 0;
      for (const it of b.items) n += estLines(it, 18, CW - 0.4);
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
    case 'note': return estLines(b.text, 15, CW) * 15 / 72 * 1.5 + 0.2;
    case 'text': return estLines(b.text, b.size || 18, CW) * (b.size || 18) / 72 * 1.5 + 0.2;
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
function renderedHeight(b, scale) {
  switch (b.type) {
    case 'bullets': {
      const pt = Math.round(18 * scale);
      let h = 0.1;
      for (const it of b.items) {
        const lines = estLines(it, pt, CW - 0.42);
        h += lines * pt / 72 * 1.5 + 0.06 + 0.08;
      }
      return h + 0.1;
    }
    case 'table': return (b.rows ? b.rows.length : 0) + (b.head ? 1 : 0) ? ((b.rows || []).length + (b.head ? 1 : 0)) * 0.46 + 0.25 : 0.25;
    case 'code': {
      const lines = String(b.text).split('\n').length;
      const ch = Math.max(0.6, lines * 0.26 * scale + 0.35);
      return ch + 0.22;
    }
    case 'note': {
      const pt = Math.round(15 * scale);
      const lines = estLines(b.text, pt, CW);
      return lines * pt / 72 * 1.5 + 0.08 + 0.12;
    }
    case 'text': {
      const pt = Math.round((b.size || 18) * scale);
      const lines = estLines(b.text, pt, CW);
      return lines * pt / 72 * 1.5 + 0.08 + 0.14;
    }
    case 'gap': return b.h || 0.2;
    case 'image': {
      const ih = b.h || ((b.w || CW * 0.6) * 0.66);
      return Math.max(ih, 0.6) + 0.2;
    }
    case 'diagram': return (b.h || 1.5) + 0.2;
    default: return 0.4;
  }
}

const deck = yaml.load(fs.readFileSync(process.argv[2], 'utf8'));
let bad = 0;
deck.slides.forEach((sl, i) => {
  const blocks = sl.blocks || [];
  const need = blocks.reduce((s, b) => s + blockHeight(b), 0);
  const avail = CONTENT_BOTTOM - BODY_TOP;
  const scale = need > avail ? Math.max(0.78, avail / need) : 1;
  const used = blocks.reduce((s, b) => s + renderedHeight(b, scale), 0);
  const bottom = BODY_TOP + used;
  const flag = bottom > 6.45 ? 'OVER' : (bottom > 6.42 ? 'warn' : 'ok  ');
  if (bottom > 6.42) bad++;
  console.log(`P${i + 1} ${flag} scale=${scale.toFixed(2)} bottom=${bottom.toFixed(2)}  ${sl.title || sl.type}`);
});
process.exit(0);
