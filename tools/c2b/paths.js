'use strict';

const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const OPTIMIZED_ROOT = path.join(PROJECT_ROOT, '课程', '课件', 'C2', 'C2-B-pro');

function assertOptimizedLessonDir(lessonDir) {
  const resolved = path.resolve(lessonDir);
  const expectedParent = path.resolve(OPTIMIZED_ROOT).toLowerCase();
  const actualParent = path.dirname(resolved).toLowerCase();
  if (actualParent !== expectedParent || !/^C2-B-(0[1-9]|10)$/.test(path.basename(resolved))) {
    throw new Error(`拒绝操作该目录；只允许读写 ${OPTIMIZED_ROOT}/C2-B-01…C2-B-10：${resolved}`);
  }
  return resolved;
}

module.exports = { PROJECT_ROOT, OPTIMIZED_ROOT, assertOptimizedLessonDir };
