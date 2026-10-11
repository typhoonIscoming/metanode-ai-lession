import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const page = fs.readFileSync(new URL('../src/app/page.tsx', import.meta.url), 'utf8');
const nextConfig = fs.readFileSync(new URL('../next.config.mjs', import.meta.url), 'utf8');

test('Run AI Strategy is click-driven and does not auto-run expensive LLM request on page load', () => {
  assert.doesNotMatch(page, /useEffect\s*\(\s*\(\)\s*=>\s*\{\s*run\(\)/);
  assert.match(page, /点击 Run AI Strategy/);
});

test('Next dev server allows 127.0.0.1 origin so client JS can hydrate in development', () => {
  assert.match(nextConfig, /allowedDevOrigins/);
  assert.match(nextConfig, /127\.0\.0\.1/);
});
