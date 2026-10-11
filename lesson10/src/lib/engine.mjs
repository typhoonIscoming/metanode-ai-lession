import fs from 'node:fs';
import path from 'node:path';
import https from 'node:https';

const STRATEGIES = ['trend_following', 'rsi_mean_reversion', 'bollinger_bands'];
const RISK_PRESETS = {
  conservative: { positionSize: 0.4, stopLoss: 0.03, fastMA: 12, slowMA: 36, window: 40 },
  balanced: { positionSize: 0.6, stopLoss: 0.04, fastMA: 10, slowMA: 30, window: 30 },
  aggressive: { positionSize: 0.8, stopLoss: 0.06, fastMA: 7, slowMA: 21, window: 20 },
};

const BASE_PRICE = { BTC: 62000, ETH: 3200, SOL: 145 };
const AIHUBMIX_CHAT_COMPLETIONS_URL = 'https://aihubmix.com/v1/chat/completions';
const DEFAULT_LLM_MODEL = 'gpt-5.5';

export function normalizeRiskProfile(value = 'balanced') {
  return ['conservative', 'balanced', 'aggressive'].includes(value) ? value : 'balanced';
}

export function normalizeSymbol(value = 'BTC') {
  const symbol = String(value).toUpperCase();
  return ['BTC', 'ETH', 'SOL'].includes(symbol) ? symbol : 'BTC';
}

export function generateMockCandles(symbol = 'BTC', length = 240) {
  const normalized = normalizeSymbol(symbol);
  const candles = [];
  const start = new Date('2024-01-01T00:00:00.000Z');
  let close = BASE_PRICE[normalized];
  for (let i = 0; i < length; i += 1) {
    const trend = 1 + i * 0.0018;
    const cycle = Math.sin(i / 9) * 0.025 + Math.sin(i / 23) * 0.018;
    const breakout = i > length * 0.62 ? (i - length * 0.62) * 0.0016 : 0;
    const nextClose = BASE_PRICE[normalized] * trend * (1 + cycle + breakout);
    const open = close;
    close = Math.max(nextClose, BASE_PRICE[normalized] * 0.45);
    const high = Math.max(open, close) * (1 + 0.006 + (i % 5) * 0.001);
    const low = Math.min(open, close) * (1 - 0.006 - (i % 3) * 0.001);
    const date = new Date(start);
    date.setUTCDate(start.getUTCDate() + i);
    candles.push({
      timestamp: date.toISOString().slice(0, 10),
      open: round(open), high: round(high), low: round(low), close: round(close),
      volume: round(10000 + i * 25 + Math.abs(Math.sin(i / 5)) * 3000),
    });
  }
  return candles;
}

export function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  const headers = lines.shift().split(',').map((h) => h.trim());
  return lines.map((line) => {
    const values = line.split(',').map((v) => v.trim());
    const row = Object.fromEntries(headers.map((h, i) => [h, values[i]]));
    return {
      timestamp: row.timestamp,
      open: Number(row.open),
      high: Number(row.high),
      low: Number(row.low),
      close: Number(row.close),
      volume: Number(row.volume),
    };
  }).filter((c) => c.timestamp && Number.isFinite(c.close) && c.close > 0)
    .sort((a, b) => String(a.timestamp).localeCompare(String(b.timestamp)));
}

export function loadCandles(symbol = 'BTC', cwd = process.cwd()) {
  const normalized = normalizeSymbol(symbol);
  const csvPath = path.join(cwd, 'data', `${normalized}.csv`);
  if (fs.existsSync(csvPath)) {
    const candles = parseCsv(fs.readFileSync(csvPath, 'utf8'));
    if (candles.length >= 60) return { candles, dataSource: 'offline_csv' };
  }
  return { candles: generateMockCandles(normalized, 240), dataSource: 'mock_data' };
}

export function sma(values, period, index = values.length - 1) {
  const end = index + 1;
  const start = Math.max(0, end - period);
  const slice = values.slice(start, end);
  return slice.reduce((sum, value) => sum + value, 0) / slice.length;
}

export function standardDeviation(values, period, index = values.length - 1) {
  const end = index + 1;
  const start = Math.max(0, end - period);
  const slice = values.slice(start, end);
  const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
  const variance = slice.reduce((sum, value) => sum + (value - mean) ** 2, 0) / slice.length;
  return Math.sqrt(variance);
}

export function rsi(values, period = 14, index = values.length - 1) {
  const start = Math.max(1, index - period + 1);
  let gains = 0;
  let losses = 0;
  let count = 0;
  for (let i = start; i <= index; i += 1) {
    const change = values[i] - values[i - 1];
    if (change >= 0) gains += change;
    else losses += Math.abs(change);
    count += 1;
  }
  const avgGain = gains / Math.max(count, 1);
  const avgLoss = losses / Math.max(count, 1);
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

export function calculateIndicators(candles) {
  const closes = candles.map((c) => c.close);
  const latestPrice = closes.at(-1);
  const maFast = sma(closes, 10);
  const maSlow = sma(closes, 30);
  const rsi14 = rsi(closes, 14);
  const bollingerMiddle = sma(closes, 20);
  const bollingerStd = standardDeviation(closes, 20);
  const bollingerUpper = bollingerMiddle + 2 * bollingerStd;
  const bollingerLower = bollingerMiddle - 2 * bollingerStd;
  const first30 = closes[Math.max(0, closes.length - 31)] || closes[0];
  const return30d = (latestPrice - first30) / first30;
  const returns = closes.slice(1).map((c, i) => (c - closes[i]) / closes[i]);
  const recent = returns.slice(-30);
  const mean = recent.reduce((s, v) => s + v, 0) / Math.max(recent.length, 1);
  const variance = recent.reduce((s, v) => s + (v - mean) ** 2, 0) / Math.max(recent.length, 1);
  const volatility30d = Math.sqrt(variance);
  let peak = closes[0];
  let maxDrawdown30d = 0;
  for (const price of closes.slice(-30)) {
    peak = Math.max(peak, price);
    maxDrawdown30d = Math.min(maxDrawdown30d, (price - peak) / peak);
  }
  const trendStrength = maFast > maSlow && return30d > 0.02 ? 'high' : Math.abs(return30d) > 0.01 ? 'medium' : 'low';
  const regime = maFast > maSlow ? (volatility30d > 0.035 ? 'uptrend_high_volatility' : 'uptrend_medium_volatility') : 'range_or_downtrend';
  return {
    latestPrice: round(latestPrice), return30d: round(return30d, 4), volatility30d: round(volatility30d, 4),
    maxDrawdown30d: round(maxDrawdown30d, 4), maFast: round(maFast), maSlow: round(maSlow),
    rsi14: round(rsi14, 2), bollingerUpper: round(bollingerUpper), bollingerMiddle: round(bollingerMiddle), bollingerLower: round(bollingerLower),
    trendStrength, regime,
  };
}

export function fallbackAdvisor({ symbol, riskProfile = 'balanced', goal = 'capture_trend', marketSummary }) {
  const risk = normalizeRiskProfile(riskProfile);
  const preset = RISK_PRESETS[risk];
  let selectedStrategy = 'trend_following';
  if (goal === 'control_drawdown' && (marketSummary.rsi14 > 70 || marketSummary.rsi14 < 35 || marketSummary.volatility30d > 0.025)) selectedStrategy = 'rsi_mean_reversion';
  if (goal === 'stable_growth' && marketSummary.trendStrength !== 'high') selectedStrategy = 'rsi_mean_reversion';
  if ((marketSummary.latestPrice > marketSummary.bollingerUpper || marketSummary.return30d > 0.14) && risk === 'aggressive') selectedStrategy = 'bollinger_bands';
  if (marketSummary.trendStrength === 'high' && marketSummary.maFast > marketSummary.maSlow) selectedStrategy = 'trend_following';

  const names = {
    trend_following: 'Trend Following',
    rsi_mean_reversion: 'RSI Mean Reversion',
    bollinger_bands: 'Bollinger Bands',
  };
  return {
    marketRegime: marketSummary.regime,
    summary: `${symbol} 当前呈现${marketSummary.maFast > marketSummary.maSlow ? '上升趋势' : '震荡/回落'}，30 日收益 ${(marketSummary.return30d * 100).toFixed(1)}%，波动率 ${(marketSummary.volatility30d * 100).toFixed(1)}%。`,
    opportunity: marketSummary.trendStrength === 'high' ? '趋势延续信号较强，适合用规则化策略捕捉主升段。' : '市场方向不够明确，更适合控制仓位并等待清晰信号。',
    risk: '本结果基于历史数据模拟，近期波动和回撤仍可能放大，需要使用止损和仓位控制。',
    selectedStrategy,
    strategyName: names[selectedStrategy],
    strategyReason: `用户选择 ${risk} 风险偏好和 ${goal} 目标，结合市场状态后推荐 ${names[selectedStrategy]}。`,
    parameters: parametersFor(selectedStrategy, risk),
    disclaimer: '仅用于教学和模拟，不构成投资建议。',
    source: 'fallback_rules',
  };
}


export async function aiHubMixAdvisor({
  symbol,
  riskProfile = 'balanced',
  goal = 'capture_trend',
  marketSummary,
  apiKey = process.env.AIHUBMIX_API_KEY,
  baseUrl = process.env.AIHUBMIX_BASE_URL || AIHUBMIX_CHAT_COMPLETIONS_URL,
  model = process.env.AIHUBMIX_MODEL || DEFAULT_LLM_MODEL,
  fetchImpl = nodeHttpsFetchJson,
} = {}) {
  if (!apiKey) throw new Error('Missing AIHUBMIX_API_KEY');
  if (typeof fetchImpl !== 'function') throw new Error('fetch is not available');

  const body = {
    model,
    messages: [
      {
        role: 'system',
        content: [
          'You are an AI strategy analyst for an educational trading simulation.',
          'You must only choose from these strategies: trend_following, rsi_mean_reversion, bollinger_bands.',
          'You must not invent new strategies.',
          'You must not provide financial advice or promise profits.',
          'All trading execution is handled by deterministic backtesting code.',
          'Return valid JSON only. Do not wrap it in markdown.',
        ].join('\n'),
      },
      {
        role: 'user',
        content: JSON.stringify({
          symbol,
          riskProfile,
          goal,
          marketSummary,
          availableStrategies: ['trend_following', 'rsi_mean_reversion', 'bollinger_bands'],
          requiredSchema: {
            marketRegime: 'string',
            summary: 'string in Chinese',
            opportunity: 'string in Chinese',
            risk: 'string in Chinese',
            selectedStrategy: 'trend_following | rsi_mean_reversion | bollinger_bands',
            strategyReason: 'string in Chinese',
            parameters: 'object matching the selected strategy',
            disclaimer: 'string in Chinese',
          },
        }),
      },
    ],
  };

  const response = await fetchImpl(baseUrl, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = typeof response.text === 'function' ? await response.text().catch(() => '') : '';
    throw new Error(`AIHubMix request failed: ${response.status} ${errorText}`.trim());
  }

  const payload = await response.json();
  const content = payload?.choices?.[0]?.message?.content;
  if (!content) throw new Error('AIHubMix response missing message content');
  const parsed = parseJsonContent(content);
  return normalizeLlmAdvice(parsed, riskProfile, marketSummary);
}


function nodeHttpsFetchJson(url, options = {}) {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const body = options.body || '';
    const req = https.request({
      hostname: target.hostname,
      port: target.port || 443,
      path: `${target.pathname}${target.search}`,
      method: options.method || 'GET',
      family: 4,
      headers: {
        ...(options.headers || {}),
        'Content-Length': Buffer.byteLength(body),
      },
    }, (res) => {
      let raw = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { raw += chunk; });
      res.on('end', () => {
        resolve({
          ok: res.statusCode >= 200 && res.statusCode < 300,
          status: res.statusCode,
          async json() { return JSON.parse(raw); },
          async text() { return raw; },
        });
      });
    });
    req.on('error', reject);
    req.setTimeout(60000, () => {
      req.destroy(new Error('AIHubMix request timed out'));
    });
    if (body) req.write(body);
    req.end();
  });
}

function parseJsonContent(content) {
  const text = String(content).trim().replace(/^```(?:json)?\s*/i, '').replace(/```$/i, '').trim();
  return JSON.parse(text);
}

function normalizeLlmAdvice(advice, riskProfile, marketSummary) {
  const selectedStrategy = STRATEGIES.includes(advice.selectedStrategy) ? advice.selectedStrategy : 'trend_following';
  const names = {
    trend_following: 'Trend Following',
    rsi_mean_reversion: 'RSI Mean Reversion',
    bollinger_bands: 'Bollinger Bands',
  };
  const safeParameters = sanitizeParameters(selectedStrategy, advice.parameters, riskProfile);
  return {
    marketRegime: String(advice.marketRegime || marketSummary.regime),
    summary: String(advice.summary || 'AI 已根据市场摘要完成判断。'),
    opportunity: String(advice.opportunity || '可在模拟环境中观察策略表现。'),
    risk: String(advice.risk || '本结果基于历史数据模拟，需要注意波动与回撤风险。'),
    selectedStrategy,
    strategyName: names[selectedStrategy],
    strategyReason: String(advice.strategyReason || `AI 推荐 ${names[selectedStrategy]}。`),
    parameters: safeParameters,
    disclaimer: String(advice.disclaimer || '仅用于教学和模拟，不构成投资建议。'),
    source: 'llm',
  };
}

function sanitizeParameters(strategy, parameters = {}, riskProfile = 'balanced') {
  const defaults = parametersFor(strategy, normalizeRiskProfile(riskProfile));
  const merged = { ...defaults, ...parameters };
  const clamp = (value, min, max, fallback) => Number.isFinite(Number(value)) ? Math.min(max, Math.max(min, Number(value))) : fallback;
  if (strategy === 'trend_following') {
    return {
      fastMA: Math.round(clamp(merged.fastMA, 3, 60, defaults.fastMA)),
      slowMA: Math.round(clamp(merged.slowMA, 5, 120, defaults.slowMA)),
      positionSize: round(clamp(merged.positionSize, 0.1, 0.9, defaults.positionSize), 4),
      stopLoss: round(clamp(merged.stopLoss, 0.01, 0.2, defaults.stopLoss), 4),
    };
  }
  if (strategy === 'rsi_mean_reversion') {
    return {
      rsiPeriod: Math.round(clamp(merged.rsiPeriod, 5, 30, defaults.rsiPeriod)),
      oversold: Math.round(clamp(merged.oversold, 10, 45, defaults.oversold)),
      overbought: Math.round(clamp(merged.overbought, 55, 90, defaults.overbought)),
      positionSize: round(clamp(merged.positionSize, 0.1, 0.9, defaults.positionSize), 4),
    };
  }
  return {
    bbWindow: Math.round(clamp(merged.bbWindow, 5, 80, defaults.bbWindow)),
    stdDev: round(clamp(merged.stdDev, 1, 4, defaults.stdDev), 2),
    positionSize: round(clamp(merged.positionSize, 0.1, 0.9, defaults.positionSize), 4),
    stopLoss: round(clamp(merged.stopLoss, 0.01, 0.2, defaults.stopLoss), 4),
  };
}

function parametersFor(strategy, risk) {
  const p = RISK_PRESETS[risk];
  if (strategy === 'rsi_mean_reversion') return { rsiPeriod: 14, oversold: risk === 'conservative' ? 25 : risk === 'balanced' ? 30 : 35, overbought: risk === 'conservative' ? 75 : risk === 'balanced' ? 70 : 65, positionSize: risk === 'conservative' ? 0.3 : risk === 'balanced' ? 0.5 : 0.7 };
  if (strategy === 'bollinger_bands') return { bbWindow: risk === 'conservative' ? 30 : risk === 'balanced' ? 20 : 14, stdDev: risk === 'conservative' ? 2.4 : risk === 'balanced' ? 2 : 1.7, positionSize: risk === 'conservative' ? 0.35 : risk === 'balanced' ? 0.55 : 0.75, stopLoss: risk === 'conservative' ? 0.03 : risk === 'balanced' ? 0.05 : 0.08 };
  return { fastMA: p.fastMA, slowMA: p.slowMA, positionSize: p.positionSize, stopLoss: p.stopLoss };
}

export function generateSignals(candles, strategy, params) {
  if (!STRATEGIES.includes(strategy)) throw new Error(`Unknown strategy: ${strategy}`);
  const signals = [];
  const closes = candles.map((c) => c.close);
  for (let i = 1; i < candles.length; i += 1) {
    let action = 'HOLD';
    let reason = 'No signal';
    if (strategy === 'trend_following') {
      const fastPrev = sma(closes, params.fastMA || 10, i - 1);
      const slowPrev = sma(closes, params.slowMA || 30, i - 1);
      const fast = sma(closes, params.fastMA || 10, i);
      const slow = sma(closes, params.slowMA || 30, i);
      if (fast >= slow && fastPrev < slowPrev) { action = 'BUY'; reason = 'Fast MA crossed above Slow MA'; }
      if (fast <= slow && fastPrev > slowPrev) { action = 'SELL'; reason = 'Fast MA crossed below Slow MA'; }
    } else if (strategy === 'rsi_mean_reversion') {
      const currentRsi = rsi(closes, params.rsiPeriod || 14, i);
      if (currentRsi <= (params.oversold ?? 30)) { action = 'BUY'; reason = 'RSI entered oversold mean-reversion zone'; }
      if (currentRsi >= (params.overbought ?? 70)) { action = 'SELL'; reason = 'RSI entered overbought exit zone'; }
    } else if (strategy === 'bollinger_bands') {
      const window = params.bbWindow || 20;
      const middle = sma(closes, window, i);
      const dev = standardDeviation(closes, window, i);
      const upper = middle + (params.stdDev || 2) * dev;
      const lower = middle - (params.stdDev || 2) * dev;
      if (closes[i] < lower) { action = 'BUY'; reason = 'Price closed below lower Bollinger Band'; }
      if (closes[i] > upper || closes[i] >= middle) { action = 'SELL'; reason = 'Price reverted toward/above Bollinger middle band'; }
    }
    signals.push({ timestamp: candles[i].timestamp, action, price: candles[i].close, reason });
  }
  if (!signals.some((s) => s.action === 'BUY')) {
    const idx = Math.floor(candles.length * 0.35);
    signals[idx] = { timestamp: candles[idx + 1].timestamp, action: 'BUY', price: candles[idx + 1].close, reason: 'Fallback demo entry signal' };
    signals[Math.floor(candles.length * 0.82)] = { timestamp: candles[Math.floor(candles.length * 0.82) + 1].timestamp, action: 'SELL', price: candles[Math.floor(candles.length * 0.82) + 1].close, reason: 'Fallback demo exit signal' };
  }
  return signals;
}

export function backtest(candles, strategy, params) {
  const signals = generateSignals(candles, strategy, params);
  let cash = 10000;
  let units = 0;
  let entryEquity = 10000;
  const fee = 0.0005;
  const slippage = 0.0002;
  const trades = [];
  const equityCurve = [];
  let wins = 0;
  let closed = 0;

  for (let i = 0; i < candles.length; i += 1) {
    const candle = candles[i];
    const signal = signals.find((s) => s.timestamp === candle.timestamp);
    if (signal?.action === 'BUY' && units === 0) {
      const budget = cash * (params.positionSize ?? 0.6);
      const exec = signal.price * (1 + slippage);
      units = (budget * (1 - fee)) / exec;
      cash -= budget;
      entryEquity = cash + units * exec;
      trades.push({ timestamp: signal.timestamp, action: 'BUY', price: round(exec), positionSize: params.positionSize ?? 0.6, reason: signal.reason });
    } else if (signal?.action === 'SELL' && units > 0) {
      const exec = signal.price * (1 - slippage);
      const proceeds = units * exec * (1 - fee);
      cash += proceeds;
      const exitEquity = cash;
      if (exitEquity > entryEquity) wins += 1;
      closed += 1;
      units = 0;
      trades.push({ timestamp: signal.timestamp, action: 'SELL', price: round(exec), positionSize: 0, reason: signal.reason });
    }
    const equity = cash + units * candle.close;
    equityCurve.push({ timestamp: candle.timestamp, equity: round(equity) });
  }
  if (units > 0) {
    const last = candles.at(-1);
    cash += units * last.close * (1 - fee);
    units = 0;
    closed += 1;
    trades.push({ timestamp: last.timestamp, action: 'SELL', price: round(last.close), positionSize: 0, reason: 'End of backtest exit' });
    equityCurve[equityCurve.length - 1].equity = round(cash);
  }
  const metrics = metricsFromEquity(equityCurve, 10000, wins, closed || trades.filter((t) => t.action === 'SELL').length, trades.length);
  return { signals, trades, equityCurve, metrics };
}

function metricsFromEquity(equityCurve, initialEquity, wins, closed, tradeCount) {
  let peak = initialEquity;
  let maxDrawdown = 0;
  for (const point of equityCurve) {
    peak = Math.max(peak, point.equity);
    maxDrawdown = Math.min(maxDrawdown, (point.equity - peak) / peak);
  }
  const finalEquity = equityCurve.at(-1).equity;
  return {
    totalReturn: round((finalEquity - initialEquity) / initialEquity, 4),
    maxDrawdown: round(maxDrawdown, 4),
    winRate: closed ? round(wins / closed, 4) : 0,
    tradeCount,
    finalEquity: round(finalEquity),
  };
}

export async function runStrategySimulation({ symbol = 'BTC', riskProfile = 'balanced', goal = 'capture_trend', env = process.env, fetchImpl = nodeHttpsFetchJson } = {}) {
  const normalizedSymbol = normalizeSymbol(symbol);
  const normalizedRisk = normalizeRiskProfile(riskProfile);
  const { candles, dataSource } = loadCandles(normalizedSymbol, process.cwd());
  const marketSummary = calculateIndicators(candles);
  let advice;
  try {
    advice = await aiHubMixAdvisor({
      symbol: normalizedSymbol,
      riskProfile: normalizedRisk,
      goal,
      marketSummary,
      apiKey: env.AIHUBMIX_API_KEY,
      baseUrl: env.AIHUBMIX_BASE_URL || AIHUBMIX_CHAT_COMPLETIONS_URL,
      model: env.AIHUBMIX_MODEL || DEFAULT_LLM_MODEL,
      fetchImpl,
    });
  } catch (error) {
    advice = fallbackAdvisor({ symbol: normalizedSymbol, riskProfile: normalizedRisk, goal, marketSummary });
    advice.fallbackReason = error?.message || 'LLM advisor failed';
  }
  const result = backtest(candles, advice.selectedStrategy, advice.parameters);
  return {
    symbol: normalizedSymbol,
    riskProfile: normalizedRisk,
    goal,
    dataSource,
    marketSummary,
    aiAnalysis: advice,
    strategy: { id: advice.selectedStrategy, name: advice.strategyName, parameters: advice.parameters },
    metrics: result.metrics,
    chart: {
      equityCurve: result.equityCurve,
      priceCurve: candles.map((c) => ({ timestamp: c.timestamp, close: c.close })),
    },
    trades: result.trades.slice(-12),
  };
}

function round(value, digits = 2) {
  return Number(Number(value).toFixed(digits));
}



