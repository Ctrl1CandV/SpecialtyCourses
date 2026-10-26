-- 802 题库数据库 schema
-- 重建库： python 工具/tiku.py init
-- 主库文件： 题库数据库/tiku.db

PRAGMA journal_mode=WAL;

-- 题目主表：全库唯一的结构化真相源
CREATE TABLE IF NOT EXISTS questions (
    id            TEXT PRIMARY KEY,          -- 唯一ID，见方案 3.5 命名规范
    source        TEXT NOT NULL,             -- 来源：真题2026/题集/408/王道/天勤/教材
    source_detail TEXT,                      -- 来源细节
    chapter       TEXT,                      -- 802章节：绪论/线性表/栈队列/串/数组广义表/树/图/查找/排序
    qtype         TEXT,                      -- 题型：选择/填空/解答/算法设计/程序阅读/综合应用
    number        TEXT,                      -- 原卷/原书题号
    difficulty    TEXT,                      -- 难度：题集①-⑤/王道星级
    tier          TEXT,                      -- 题集分档：一档/二档/三档
    stem          TEXT NOT NULL,             -- 题干(markdown，代码用```围栏)
    options       TEXT,                      -- 选项(选择题)
    answer        TEXT,                      -- 答案
    analysis      TEXT,                      -- 解析
    kaodian       TEXT,                      -- 考点标签，逗号分隔
    template      TEXT,                      -- 关联15模板编号(框架2.5)
    figures       TEXT,                      -- 图引用，JSON数组，相对 images/
    pdf_page      INTEGER,                   -- 原PDF页码，回溯用
    real_related  TEXT,                      -- 真题同源标注
    raw_text      TEXT,                      -- 原始识别文本(未清洗)，备查
    notes         TEXT,                      -- 备注(回忆版缺漏/识别存疑)
    created_at    TEXT DEFAULT (datetime('now','localtime'))
);

-- 章节表：802知识体系(八章)，freq来自 重邮数据结构.md 高频/中频标注
CREATE TABLE IF NOT EXISTS chapters (
    name      TEXT PRIMARY KEY,
    order_num INTEGER,
    freq      TEXT
);

-- 来源台账：每个源文件的转化状态
CREATE TABLE IF NOT EXISTS sources (
    source          TEXT PRIMARY KEY,
    file_path       TEXT,
    total_questions INTEGER DEFAULT 0,
    converted       INTEGER DEFAULT 0,
    method          TEXT,                    -- fitz/mineru/联网
    status          TEXT,                    -- 待转化/识别中/已入库
    notes           TEXT
);

-- 图片登记表(可选VLM描述)
CREATE TABLE IF NOT EXISTS figures (
    id          TEXT PRIMARY KEY,
    question_id TEXT,
    path        TEXT,
    page        INTEGER,
    desc        TEXT
);

CREATE INDEX IF NOT EXISTS idx_q_chapter  ON questions(chapter);
CREATE INDEX IF NOT EXISTS idx_q_qtype    ON questions(qtype);
CREATE INDEX IF NOT EXISTS idx_q_tier     ON questions(tier);
CREATE INDEX IF NOT EXISTS idx_q_source   ON questions(source);
CREATE INDEX IF NOT EXISTS idx_q_template ON questions(template);
CREATE INDEX IF NOT EXISTS idx_q_kaodian  ON questions(kaodian);

-- 初始化八章(freq 为初判，后续按 重邮数据结构.md 标注校准)
INSERT OR IGNORE INTO chapters (name, order_num, freq) VALUES
 ('绪论',      1, '中频'),
 ('线性表',    2, '高频'),
 ('栈队列',    3, '高频'),
 ('串',        4, '中频'),
 ('数组广义表',5, '中频'),
 ('树',        6, '高频'),
 ('图',        7, '高频'),
 ('查找',      8, '高频'),
 ('排序',      9, '高频');
