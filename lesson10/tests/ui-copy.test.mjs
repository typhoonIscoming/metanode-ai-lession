import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const page = fs.readFileSync(new URL('../src/app/page.tsx', import.meta.url), 'utf8');

test('cockpit page clearly labels the final AI selected strategy', () => {
  assert.match(page, /AI 最终选择的策略/);
  assert.match(page, /Strategy ID/);
  assert.match(page, /AI Selection Source/);
});
