#!/usr/bin/env node
// check.js —— 课件自检工具
// 用法: node check.js [课件目录]
//   不传参：检查 课件/ 下所有节
//   传参：检查指定目录，如 node check.js ..\课件\C1\C1-A-02
// 检查项：
//   1. deck.yaml 能否被 js-yaml 正常解析
//   2. 渲染是否无报错（调用 render-pptx.js）
//   3. deck slides 数 == 讲稿 P 小节数
//   4. 讲稿字数是否达到时长预算下限（160字/分）
//   5. 违禁词扫描（营销腔、AI味结构词）
//   6. 内部代号泄漏（C1-A/C2-B 等，deck 与讲稿都不应出现）
//   7. 讲稿每个 P 小节是否有页名
//   8. image 块的 src 路径是否存在
//   9. 讲稿前向引用钩子重复（"后面会讲"类铺垫过多则告警）
//   10. 讲稿加粗密度（格式过度则告警）
//   11. 讲稿"绕"口禁语（比喻替代术语/AI专用词，见授课技法指南§4.7）
//   12. 讲稿正文未转义的指针星号（应写 \*，见授课技法指南§4.6第8条）
//   13. deck 制作备注混进学生页（动画登记类文字只该进讲稿课前准备）
//   注：第11—13项对已录制封存的课节不追溯（封存课件不回改）
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const COURSE_DIR = path.join(ROOT, '课件');

// 违禁词（营销腔 + AI味结构词）
const BAD_WORDS = /稳稳拿下|放心跟|跑不掉|一句话总结|首先，|其次，|综上所述|值得注意的是|不仅.*而且|总而言之/g;
// 内部代号（面向学生不应出现，deck.meta.id 是渲染元数据不上页面）
const INTERNAL_CODES = /C1-A|C1-B|C2-A|C2-B|C2-C|C3-A|C3-B|C3-C/g;
// "绕"口禁语（第十轮：取自 C1-B-02 取证的高信号固定说法，替换对照表见授课技法指南§4.7）
const ROUND_WORDS = /路线报一下|盘点.{0,6}问题|立(一个|个)规矩|规矩就一条|规矩记住|数学基础|设计哲学|自由翻译|按现在的值办事|办完事再|不管三七二十一|的脾气是|小尾巴|窗户纸|骨子里|新家具|新零件|构建这个画面|分界线就在|再交手|严丝合缝|家常便饭|才算真懂|压着没讲/g;
// 已录制封存的课节：第十轮新增的第11—13项不追溯，避免产生不可修的告警
const SEALED = /C0-代码班总先导|C1-A-0\d|802备考经验分享/;
// deck 制作备注（学生页不应出现；注意不收 "占位"，会与 C 语言术语"占位符"相冲）
const DECK_PROD_NOTES = /本页|逐条动画|不手写|配合讲稿|录制|口播|讲稿|待补/;

const results = []; // {dir, level, msg}

function log(dir, level, msg) {
  results.push({ dir, level, msg });
}

// 扫描所有课件目录
function findDecks(baseDir) {
  const decks = [];
  function walk(dir) {
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.name === 'deck.yaml') decks.push(path.dirname(full));
    }
  }
  walk(baseDir);
  return decks;
}

// 从 deck.meta.duration 提取分钟数
function parseDuration(str) {
  if (!str) return 0;
  const m = String(str).match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

// 讲稿字数（仅汉字）
function countChinese(text) {
  return (String(text).match(/[\u4e00-\u9fa5]/g) || []).length;
}

// 统计 deck slides 数（顶层 - type:）
function countSlides(deckText) {
  return (String(deckText).match(/^  - type:/gm) || []).length;
}

// 统计讲稿 P 小节数
function countPSections(mdText) {
  return (String(mdText).match(/^## P\d+/gm) || []).length;
}

function checkDeck(dir) {
  const deckPath = path.join(dir, 'deck.yaml');
  const baseName = path.basename(dir);

  // 找讲稿文件：{dir}/{baseName}-讲稿.md
  const mdPath = path.join(dir, `${baseName}-讲稿.md`);

  // 1. YAML 解析
  let deck;
  let deckText;
  try {
    deckText = fs.readFileSync(deckPath, 'utf8');
    deck = yaml.load(deckText);
  } catch (e) {
    log(dir, 'ERROR', `deck.yaml 解析失败: ${e.message}`);
    return;
  }

  // 2. 渲染检查
  try {
    execSync(`node "${path.join(__dirname, 'render-pptx.js')}" "${deckPath}"`, { stdio: 'pipe', cwd: __dirname });
  } catch (e) {
    log(dir, 'ERROR', `渲染失败: ${e.stderr ? e.stderr.toString().split('\n')[0] : e.message}`);
  }

  // 3. slides 数 vs 讲稿 P 数
  const slides = countSlides(deckText);
  let pSections = 0;
  let mdText = '';
  if (fs.existsSync(mdPath)) {
    mdText = fs.readFileSync(mdPath, 'utf8');
    pSections = countPSections(mdText);
  } else {
    log(dir, 'WARN', `讲稿文件不存在: ${baseName}-讲稿.md`);
  }
  if (pSections > 0 && slides !== pSections) {
    log(dir, 'ERROR', `页数不一致: deck=${slides}页, 讲稿=${pSections}个P小节`);
  }

  // 4. 讲稿字数 vs 时长预算
  const duration = deck.meta ? parseDuration(deck.meta.duration) : 0;
  if (duration > 0 && mdText) {
    const zhCount = countChinese(mdText);
    const minWords = duration * 160;
    if (zhCount < minWords) {
      log(dir, 'WARN', `讲稿字数偏少: ${zhCount}字, ${duration}分钟建议≥${minWords}字 (差${minWords - zhCount}字)`);
    }
  }

  // 5. 违禁词
  const checkBad = (text, fileLabel) => {
    const matches = String(text).match(BAD_WORDS);
    if (matches) log(dir, 'WARN', `${fileLabel} 含违禁词: ${[...new Set(matches)].join('、')}`);
  };
  checkBad(deckText, 'deck.yaml');
  if (mdText) checkBad(mdText, '讲稿');

  // 6. 内部代号（讲稿正文不应出现；deck 中 meta.id 是允许的，只扫 slides 内容区）
  if (mdText) {
    const codeMatches = mdText.match(INTERNAL_CODES);
    if (codeMatches) log(dir, 'WARN', `讲稿含内部代号: ${[...new Set(codeMatches)].join('、')}`);
  }
  // deck 内容区扫描：去掉 meta 段
  const deckBody = String(deckText).replace(/^meta:[\s\S]*?^slides:/m, 'slides:');
  const deckCodeMatches = deckBody.match(INTERNAL_CODES);
  if (deckCodeMatches) log(dir, 'WARN', `deck内容区含内部代号: ${[...new Set(deckCodeMatches)].join('、')}`);

  // 7. 讲稿 P 小节页名
  if (mdText) {
    const pNoName = /^\s*##\s*P\d+\s*$/gm;
    if (pNoName.test(mdText)) log(dir, 'WARN', '讲稿存在无页名的 P 小节');
  }

  // 8. image 块 src 存在性
  for (const sl of (deck.slides || [])) {
    for (const b of (sl.blocks || [])) {
      if (b.type === 'image') {
        const src = b.src || b.path;
        if (!src) { log(dir, 'WARN', `image块缺少src (页: ${sl.title || ''})`); continue; }
        const imgPath = path.isAbsolute(src) ? src : path.join(ROOT, src);
        if (!fs.existsSync(imgPath)) log(dir, 'WARN', `image路径不存在: ${src} (页: ${sl.title || ''})`);
      }
    }
  }

  // 9. 前向引用钩子重复（基础阶段复盘：同一"后面再说"钩子被反复铺垫）
  if (mdText) {
    const body = mdText.split(/^## 附录/m)[0]; // 附录不计
    const FWD = /揭晓|留到|后面再说|用到时再|下一节讲|下次讲|强化阶段.{0,4}讲|后面.{0,8}讲/g;
    const fwdCount = (body.match(FWD) || []).length;
    if (fwdCount > 4) log(dir, 'WARN', `讲稿"后面会讲"类前向引用出现 ${fwdCount} 次（>4），对照悬念台账检查是否重复铺垫`);
  }

  // 10. 讲稿加粗密度（基础阶段复盘：格式过度AI化）
  if (mdText) {
    const boldCount = (mdText.match(/\*\*/g) || []).length / 2;
    if (boldCount > 10) log(dir, 'WARN', `讲稿加粗 ${boldCount} 处（>10），格式过度，见授课技法指南§4.6`);
  }

  // 11. "绕"口禁语（第十轮：比喻替代术语与AI专用词，型一/型三仍需人工朗读自查）
  const sealed = SEALED.test(dir) || SEALED.test(baseName);
  if (mdText && !sealed) {
    const roundMatches = mdText.match(ROUND_WORDS);
    if (roundMatches) {
      log(dir, 'WARN', `讲稿含"绕"口禁语 ${roundMatches.length} 处: ${[...new Set(roundMatches)].join('、')}（改法见授课技法指南§4.7对照表）`);
    }
  }

  // 12. 讲稿正文未转义的指针星号（排除代码围栏、行内代码与加粗标记）
  if (mdText && !sealed) {
    const prose = mdText
      .replace(/```[\s\S]*?```/g, '')   // 代码围栏
      .replace(/`[^`\n]+`/g, '')          // 行内代码
      .replace(/\*\*[^*\n]+\*\*/g, '');   // 加粗标记
    const bareStars = (prose.match(/(?<!\\)\*/g) || []).length;
    if (bareStars > 0) {
      log(dir, 'WARN', `讲稿正文有 ${bareStars} 处未转义的 * ，指针与解引用应写 \\*（见授课技法指南§4.6第8条）`);
    }
  }

  // 13. deck 制作备注混进学生页（第十轮：B-01/B-02/B-04/B-06 均查到"本页逐条动画出现"类备注印在标题上）
  if (!sealed) {
    const notes = String(deckText).replace(/^meta:[\s\S]*?^slides:/m, 'slides:')
      .split('\n').filter(l => DECK_PROD_NOTES.test(l)).map(l => l.trim());
    if (notes.length) {
      log(dir, 'WARN', `deck 含制作备注 ${notes.length} 处（学生页不应出现，动画登记只进讲稿课前准备）: ${notes[0]}`);
    }
  }
}

// ---- 主流程 ----
const targetDir = process.argv[2];
const dirs = targetDir
  ? [path.resolve(targetDir)]
  : findDecks(COURSE_DIR);

if (dirs.length === 0) {
  console.error('未找到任何 deck.yaml');
  process.exit(1);
}

for (const d of dirs) checkDeck(d);

// 汇总输出
let errors = 0, warns = 0;
const byDir = {};
for (const r of results) {
  if (!byDir[r.dir]) byDir[r.dir] = [];
  byDir[r.dir].push(r);
  if (r.level === 'ERROR') errors++;
  else if (r.level === 'WARN') warns++;
}

console.log('=========================================');
console.log('课件自检报告');
console.log('=========================================');
for (const d of dirs) {
  const shortName = path.relative(COURSE_DIR, d) || path.basename(d);
  const items = byDir[d] || [];
  if (items.length === 0) {
    console.log(`\n[OK] ${shortName} —— 全部通过`);
  } else {
    console.log(`\n${shortName}:`);
    for (const it of items) console.log(`  [${it.level}] ${it.msg}`);
  }
}
console.log('\n-----------------------------------------');
console.log(`检查 ${dirs.length} 节课 | ERROR ${errors} | WARN ${warns}`);
console.log(errors > 0 ? '❌ 存在错误，需修复' : (warns > 0 ? '⚠ 有警告，请查看' : '✅ 全部通过'));
process.exit(errors > 0 ? 1 : 0);
