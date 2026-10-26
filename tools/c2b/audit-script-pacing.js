// Read-only per-page manuscript audit. Counts only the heading's own section;
// non-speaking answer pages and later appendices never spill into the last page.
'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require(path.join(path.resolve(__dirname, '..', '..'), 'tools', 'node_modules', 'js-yaml'));
const { OPTIMIZED_ROOT, assertOptimizedLessonDir } = require('./paths.js');

function countChinese(text) { return (text.match(/[\u3400-\u9fff]/g) || []).length; }
function parseMinutes(raw) {
  const match = String(raw).match(/^\s*(\d+)\s*(?:min|分钟)/i);
  if (!match) throw new Error(`无法读取 meta.duration: ${raw}`);
  return Number(match[1]);
}

const lessons = process.argv.slice(2).length
  ? process.argv.slice(2)
  : Array.from({ length: 10 }, (_, i) => `C2-B-${String(i + 1).padStart(2, '0')}`);
let failed = false;

for (const item of lessons) {
  let dir;
  try {
    dir = assertOptimizedLessonDir(path.isAbsolute(item) || item.includes(path.sep)
      ? item
      : path.join(OPTIMIZED_ROOT, item));
  } catch (error) {
    console.error(error.message);
    failed = true;
    continue;
  }
  const id = path.basename(dir);
  const scriptPath = path.join(dir, `${id}-讲稿.md`);
  const deckPath = path.join(dir, 'deck.yaml');
  if (!fs.existsSync(scriptPath) || !fs.existsSync(deckPath)) {
    console.error(`${id}: 缺少讲稿或 deck.yaml`);
    failed = true;
    continue;
  }

  const manuscript = fs.readFileSync(scriptPath, 'utf8');
  const deck = yaml.load(fs.readFileSync(deckPath, 'utf8'));
  const headings = [...manuscript.matchAll(/^## (P\d+)\b([^\n]*)$/gm)];
  const pageIds = headings.map(match => Number(match[1].slice(1)));
  const expectedIds = (deck.slides || []).map((_, i) => i + 1);
  const orderOkay = JSON.stringify(pageIds) === JSON.stringify(expectedIds);
  if (!orderOkay) failed = true;

  let minuteSum = 0;
  const report = [];
  for (let i = 0; i < headings.length; i++) {
    const heading = headings[i];
    const start = heading.index + heading[0].length;
    const end = i + 1 < headings.length ? headings[i + 1].index : manuscript.search(/^## (?!P\d+\b)/m) < 0
      ? manuscript.length
      : manuscript.search(/^## (?!P\d+\b)/m);
    const body = manuscript.slice(start, end)
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`[^`]*`/g, '');
    const timeMatch = heading[2].match(/（约\s*(\d+)\s*分钟）/);
    const spoken = !/不口播/.test(heading[2]);
    const minutes = timeMatch ? Number(timeMatch[1]) : 0;
    minuteSum += minutes;
    const chars = countChinese(body);
    report.push(`P${pageIds[i]} ${spoken ? `${minutes || '未标'}min` : '不口播'} ${chars}字`);
  }

  let deckMinutes;
  try { deckMinutes = parseMinutes(deck.meta.duration); }
  catch (error) { console.error(`${id}: ${error.message}`); failed = true; continue; }
  const timeOkay = minuteSum === deckMinutes;
  if (!timeOkay) failed = true;
  console.log(`\n${id} | ${headings.length}/${expectedIds.length} 页 | ${minuteSum}/${deckMinutes}min | 页序 ${orderOkay ? '正常' : '异常'}`);
  console.log(report.join(' | '));
}

if (failed) process.exitCode = 1;
console.log('\n字数与每分钟汉字数仅作回看线索；是否增删内容按讲解、推演和练习核对，不按字数定质量。');
