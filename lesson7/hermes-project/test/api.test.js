import test from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../src/app.js';

test('GET /api/tokens returns cached token heatmap payload', async () => {
  const app = createApp({
    tokenStore: {
      getSnapshot() {
        return {
          source: 'test-source',
          updatedAt: '2026-01-02T03:04:05.000Z',
          count: 1,
          tokens: [{ rank: 1, symbol: 'BTC', name: 'BTC', price: 100000, marketValue: 1000, change24h: 1.23 }]
        };
      },
      refreshNow: async () => {}
    }
  });

  const server = app.listen(0);
  try {
    const { port } = server.address();
    const res = await fetch(`http://127.0.0.1:${port}/api/tokens`);
    const data = await res.json();

    assert.equal(res.status, 200);
    assert.equal(data.count, 1);
    assert.equal(data.tokens[0].symbol, 'BTC');
    assert.equal(data.tokens[0].change24h, 1.23);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
