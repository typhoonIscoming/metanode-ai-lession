import test from 'node:test';
import assert from 'node:assert/strict';
import { aiHubMixAdvisor, runStrategySimulation } from '../src/lib/engine.mjs';

const marketSummary = {
  latestPrice: 68420,
  return30d: 0.124,
  volatility30d: 0.038,
  maxDrawdown30d: -0.071,
  maFast: 67120,
  maSlow: 64200,
  trendStrength: 'high',
  regime: 'uptrend_medium_volatility',
};

test('aiHubMixAdvisor calls AIHubMix chat completions with gpt-5.5 and parses strategy JSON', async () => {
  const calls = [];
  const fakeFetch = async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      async json() {
        return {
          choices: [{
            message: {
              content: JSON.stringify({
                marketRegime: 'uptrend_medium_volatility',
                summary: 'LLM 判断 BTC 处于上升趋势。',
                opportunity: '趋势仍有延续可能。',
                risk: '波动率上升，需要控制仓位。',
                selectedStrategy: 'bollinger_bands',
                strategyReason: 'AI 认为布林带策略更适合当前波动环境。',
                parameters: { bbWindow: 20, stdDev: 2, positionSize: 0.55, stopLoss: 0.05 },
                disclaimer: '仅用于教学和模拟，不构成投资建议。'
              })
            }
          }]
        };
      }
    };
  };

  const advice = await aiHubMixAdvisor({
    symbol: 'BTC',
    riskProfile: 'balanced',
    goal: 'capture_trend',
    marketSummary,
    apiKey: 'test-key',
    fetchImpl: fakeFetch,
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, 'https://aihubmix.com/v1/chat/completions');
  assert.equal(calls[0].options.headers.Authorization, 'Bearer test-key');
  const body = JSON.parse(calls[0].options.body);
  assert.equal(body.model, 'gpt-5.5');
  assert.equal(advice.source, 'llm');
  assert.equal(advice.selectedStrategy, 'bollinger_bands');
  assert.equal(advice.parameters.positionSize, 0.55);
});

test('runStrategySimulation uses LLM advisor when AIHUBMIX_API_KEY is configured', async () => {
  const fakeFetch = async () => ({
    ok: true,
    async json() {
      return {
        choices: [{
          message: {
            content: JSON.stringify({
              marketRegime: 'uptrend_medium_volatility',
              summary: 'LLM 真实判断：趋势较强。',
              opportunity: '可尝试趋势跟随。',
              risk: '注意回撤。',
              selectedStrategy: 'trend_following',
              strategyReason: 'AI 根据均线和风险偏好选择趋势跟随。',
              parameters: { fastMA: 10, slowMA: 30, positionSize: 0.6, stopLoss: 0.04 },
              disclaimer: '仅用于教学和模拟，不构成投资建议。'
            })
          }
        }]
      };
    }
  });

  const result = await runStrategySimulation({
    symbol: 'BTC',
    riskProfile: 'balanced',
    goal: 'capture_trend',
    env: { AIHUBMIX_API_KEY: 'test-key' },
    fetchImpl: fakeFetch,
  });

  assert.equal(result.aiAnalysis.source, 'llm');
  assert.equal(result.strategy.id, 'trend_following');
  assert.ok(result.metrics.tradeCount > 0);
});

