import test from 'node:test';
import assert from 'node:assert/strict';
import { createTokenSnapshot, filterTopTokens, normalizeSymbol } from '../src/token-service.js';

test('normalizeSymbol converts USDT trading pair to base token', () => {
  assert.equal(normalizeSymbol('BTCUSDT'), 'BTC');
  assert.equal(normalizeSymbol('ETHUSDC'), 'ETH');
});

test('filterTopTokens keeps active USDT spot pairs, excludes leveraged/stable tokens, sorts by quote volume', () => {
  const tickers = [
    { symbol: 'ETHUSDT', lastPrice: '3000', priceChangePercent: '2', quoteVolume: '9000', volume: '3', highPrice: '3100', lowPrice: '2900' },
    { symbol: 'BTCUSDT', lastPrice: '100000', priceChangePercent: '-1.5', quoteVolume: '20000', volume: '0.2', highPrice: '102000', lowPrice: '98000' },
    { symbol: 'BULLUSDT', lastPrice: '1', priceChangePercent: '10', quoteVolume: '99999', volume: '1', highPrice: '1', lowPrice: '1' },
    { symbol: 'USDCUSDT', lastPrice: '1', priceChangePercent: '0', quoteVolume: '50000', volume: '1', highPrice: '1', lowPrice: '1' },
    { symbol: 'SOLBTC', lastPrice: '0.001', priceChangePercent: '1', quoteVolume: '1000', volume: '1', highPrice: '1', lowPrice: '1' }
  ];
  const exchangeSymbols = [
    { symbol: 'BTCUSDT', status: 'TRADING', isSpotTradingAllowed: true },
    { symbol: 'ETHUSDT', status: 'TRADING', isSpotTradingAllowed: true },
    { symbol: 'BULLUSDT', status: 'TRADING', isSpotTradingAllowed: true },
    { symbol: 'USDCUSDT', status: 'TRADING', isSpotTradingAllowed: true },
    { symbol: 'SOLBTC', status: 'TRADING', isSpotTradingAllowed: true }
  ];

  const tokens = filterTopTokens(tickers, exchangeSymbols, 2);

  assert.deepEqual(tokens.map((token) => token.symbol), ['BTC', 'ETH']);
  assert.equal(tokens[0].rank, 1);
  assert.equal(tokens[0].change24h, -1.5);
  assert.equal(tokens[0].marketValue, 20000);
});

test('createTokenSnapshot returns API-ready top token payload with metadata', () => {
  const snapshot = createTokenSnapshot({
    tickers: [
      { symbol: 'BTCUSDT', lastPrice: '100000', priceChangePercent: '4.2', quoteVolume: '30000', volume: '0.3', highPrice: '101000', lowPrice: '95000' }
    ],
    exchangeSymbols: [{ symbol: 'BTCUSDT', status: 'TRADING', isSpotTradingAllowed: true }],
    limit: 1,
    now: new Date('2026-01-02T03:04:05.000Z')
  });

  assert.equal(snapshot.source, 'Binance Spot 24hr ticker');
  assert.equal(snapshot.updatedAt, '2026-01-02T03:04:05.000Z');
  assert.equal(snapshot.count, 1);
  assert.equal(snapshot.tokens[0].symbol, 'BTC');
  assert.equal(snapshot.tokens[0].change24h, 4.2);
});
