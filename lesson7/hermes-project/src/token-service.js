const BINANCE_BASE_URL = 'https://api.binance.com';
const DEFAULT_REFRESH_MS = 60_000;
const STABLE_OR_FIAT = new Set([
  'USDT', 'USDC', 'FDUSD', 'BUSD', 'TUSD', 'DAI', 'USDP', 'EUR', 'TRY', 'BRL', 'GBP', 'AUD', 'UAH', 'RUB', 'JPY', 'ARS', 'MXN', 'ZAR', 'PLN', 'RON'
]);
const LEVERAGED_SUFFIXES = ['UP', 'DOWN', 'BULL', 'BEAR'];

export function normalizeSymbol(symbol) {
  for (const quote of ['USDT', 'USDC', 'FDUSD', 'BUSD']) {
    if (symbol.endsWith(quote)) return symbol.slice(0, -quote.length);
  }
  return symbol;
}

function isSupportedToken(base) {
  if (!base || STABLE_OR_FIAT.has(base)) return false;
  return !LEVERAGED_SUFFIXES.some((suffix) => base.endsWith(suffix));
}

function activeSpotUsdtSymbols(exchangeSymbols = []) {
  return new Set(
    exchangeSymbols
      .filter((item) => item.status === 'TRADING' && item.isSpotTradingAllowed !== false && item.symbol?.endsWith('USDT'))
      .map((item) => item.symbol)
  );
}

function numberFrom(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function filterTopTokens(tickers, exchangeSymbols, limit = 100) {
  const activeSymbols = activeSpotUsdtSymbols(exchangeSymbols);
  return tickers
    .filter((ticker) => ticker.symbol?.endsWith('USDT'))
    .filter((ticker) => activeSymbols.size === 0 || activeSymbols.has(ticker.symbol))
    .map((ticker) => {
      const base = normalizeSymbol(ticker.symbol);
      return {
        base,
        ticker,
        marketValue: numberFrom(ticker.quoteVolume)
      };
    })
    .filter(({ base, marketValue }) => isSupportedToken(base) && marketValue > 0)
    .sort((a, b) => b.marketValue - a.marketValue)
    .slice(0, limit)
    .map(({ base, ticker, marketValue }, index) => ({
      rank: index + 1,
      symbol: base,
      name: base,
      pair: ticker.symbol,
      price: numberFrom(ticker.lastPrice),
      change24h: numberFrom(ticker.priceChangePercent),
      marketValue,
      quoteVolume24h: marketValue,
      baseVolume24h: numberFrom(ticker.volume),
      high24h: numberFrom(ticker.highPrice),
      low24h: numberFrom(ticker.lowPrice)
    }));
}

export function createTokenSnapshot({ tickers, exchangeSymbols, limit = 100, now = new Date() }) {
  const tokens = filterTopTokens(tickers, exchangeSymbols, limit);
  return {
    source: 'Binance Spot 24hr ticker',
    metric: 'quoteVolume24h',
    metricLabel: '24h USDT 成交额（Binance 不直接提供市值，前端用它作为市值风格色块面积）',
    updatedAt: now.toISOString(),
    count: tokens.length,
    tokens
  };
}

async function fetchJson(url, fetchImpl = fetch) {
  const response = await fetchImpl(url);
  if (!response.ok) throw new Error(`Binance request failed: ${response.status} ${response.statusText}`);
  return response.json();
}

export async function fetchBinanceSnapshot({ limit = 100, fetchImpl = fetch, now = new Date() } = {}) {
  const [tickers, exchangeInfo] = await Promise.all([
    fetchJson(`${BINANCE_BASE_URL}/api/v3/ticker/24hr`, fetchImpl),
    fetchJson(`${BINANCE_BASE_URL}/api/v3/exchangeInfo`, fetchImpl)
  ]);
  return createTokenSnapshot({ tickers, exchangeSymbols: exchangeInfo.symbols ?? [], limit, now });
}

export class TokenStore {
  constructor({ refreshMs = DEFAULT_REFRESH_MS, limit = 100, fetchImpl = fetch, logger = console } = {}) {
    this.refreshMs = refreshMs;
    this.limit = limit;
    this.fetchImpl = fetchImpl;
    this.logger = logger;
    this.snapshot = null;
    this.lastError = null;
    this.timer = null;
    this.refreshing = null;
  }

  getSnapshot() {
    return this.snapshot;
  }

  getLastError() {
    return this.lastError;
  }

  async refreshNow() {
    if (this.refreshing) return this.refreshing;
    this.refreshing = fetchBinanceSnapshot({ limit: this.limit, fetchImpl: this.fetchImpl })
      .then((snapshot) => {
        this.snapshot = snapshot;
        this.lastError = null;
        return snapshot;
      })
      .catch((error) => {
        this.lastError = { message: error.message, at: new Date().toISOString() };
        this.logger.warn?.('Token refresh failed:', error.message);
        throw error;
      })
      .finally(() => {
        this.refreshing = null;
      });
    return this.refreshing;
  }

  start() {
    if (this.timer) return;
    this.refreshNow().catch(() => {});
    this.timer = setInterval(() => this.refreshNow().catch(() => {}), this.refreshMs);
    this.timer.unref?.();
  }

  stop() {
    if (!this.timer) return;
    clearInterval(this.timer);
    this.timer = null;
  }
}
