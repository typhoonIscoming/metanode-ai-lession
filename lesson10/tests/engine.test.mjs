import test from 'node:test';
import assert from 'node:assert/strict';
import { generateMockCandles, calculateIndicators, fallbackAdvisor, runStrategySimulation } from '../src/lib/engine.mjs';

test('generateMockCandles creates sorted OHLCV candles with requested length', () => {
  const candles = generateMockCandles('BTC', 120);
  assert.equal(candles.length, 120);
  assert.ok(candles[0].timestamp < candles[119].timestamp);
  assert.ok(candles.every((c) => c.high >= c.low && c.close > 0 && c.volume > 0));
});

test('calculateIndicators identifies an upward trending market summary', () => {
  const candles = generateMockCandles('BTC', 180);
  const summary = calculateIndicators(candles);
  assert.equal(summary.trendStrength, 'high');
  assert.ok(summary.maFast > summary.maSlow);
  assert.ok(summary.latestPrice > 0);
});

test('fallbackAdvisor selects a valid strategy and risk-adjusted parameters', () => {
  const candles = generateMockCandles('BTC', 180);
  const summary = calculateIndicators(candles);
  const advice = fallbackAdvisor({ symbol: 'BTC', riskProfile: 'balanced', goal: 'capture_trend', marketSummary: summary });
  assert.equal(advice.selectedStrategy, 'trend_following');
  assert.equal(advice.parameters.positionSize, 0.6);
  assert.match(advice.summary, /趋势|trend/i);
});

test('runStrategySimulation returns cockpit-ready analysis, metrics, chart and trades', async () => {
  const result = await runStrategySimulation({ symbol: 'BTC', riskProfile: 'balanced', goal: 'capture_trend' });
  assert.equal(result.symbol, 'BTC');
  assert.ok(['offline_csv', 'mock_data'].includes(result.dataSource));
  assert.equal(result.aiAnalysis.selectedStrategy, 'trend_following');
  assert.ok(result.metrics.tradeCount > 0);
  assert.ok(result.metrics.finalEquity > 0);
  assert.ok(result.chart.equityCurve.length > 50);
  assert.ok(result.trades.some((t) => t.action === 'BUY'));
});


test('calculateIndicators includes professional RSI and Bollinger Bands fields', () => {
  const candles = generateMockCandles('BTC', 180);
  const summary = calculateIndicators(candles);
  assert.ok(summary.rsi14 >= 0 && summary.rsi14 <= 100);
  assert.ok(summary.bollingerUpper > summary.bollingerMiddle);
  assert.ok(summary.bollingerMiddle > summary.bollingerLower);
});
