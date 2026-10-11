const state = { tokens: [], sort: 'rank', query: '' };
const els = {
  heatmap: document.querySelector('#heatmap'),
  status: document.querySelector('#status'),
  updatedAt: document.querySelector('#updatedAt'),
  count: document.querySelector('#count'),
  metricLabel: document.querySelector('#metricLabel'),
  refreshBtn: document.querySelector('#refreshBtn'),
  searchInput: document.querySelector('#searchInput'),
  sortSelect: document.querySelector('#sortSelect')
};

function formatMoney(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 2 }).format(value);
}

function formatPrice(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumSignificantDigits: 6 }).format(value);
}

function tileSize(rank) {
  if (rank <= 8) return 'large';
  if (rank <= 30) return 'medium';
  return 'small';
}

function directionClass(change) {
  if (change > 0.15) return 'up';
  if (change < -0.15) return 'down';
  return 'flat';
}

function visibleTokens() {
  const q = state.query.trim().toUpperCase();
  const filtered = q ? state.tokens.filter((token) => token.symbol.includes(q) || token.pair.includes(q)) : [...state.tokens];
  if (state.sort === 'changeDesc') filtered.sort((a, b) => b.change24h - a.change24h);
  if (state.sort === 'changeAsc') filtered.sort((a, b) => a.change24h - b.change24h);
  if (state.sort === 'rank') filtered.sort((a, b) => a.rank - b.rank);
  return filtered;
}

function render() {
  const tokens = visibleTokens();
  els.heatmap.innerHTML = tokens.map((token) => {
    const change = `${token.change24h >= 0 ? '+' : ''}${token.change24h.toFixed(2)}%`;
    return `<article class="tile ${tileSize(token.rank)} ${directionClass(token.change24h)}" title="${token.symbol} · ${change} · ${formatMoney(token.marketValue)}">
      <div class="rank">#${token.rank} · ${token.pair}</div>
      <div class="symbol">${token.symbol}</div>
      <div class="price">${formatPrice(token.price)}</div>
      <div class="change">${change}</div>
      <div class="volume">24h ${formatMoney(token.marketValue)}</div>
    </article>`;
  }).join('');
}

async function loadTokens({ force = false } = {}) {
  els.status.className = 'status';
  els.status.textContent = force ? '正在刷新 Binance 数据...' : '正在加载 Binance 数据...';
  try {
    const response = await fetch(force ? '/api/refresh' : '/api/tokens', { method: force ? 'POST' : 'GET' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.error || '请求失败');
    state.tokens = data.tokens;
    els.updatedAt.textContent = new Date(data.updatedAt).toLocaleString();
    els.count.textContent = data.count;
    els.metricLabel.textContent = data.metricLabel;
    els.status.className = 'status hidden';
    render();
  } catch (error) {
    els.status.className = 'status error';
    els.status.textContent = `加载失败：${error.message}`;
  }
}

els.searchInput.addEventListener('input', (event) => { state.query = event.target.value; render(); });
els.sortSelect.addEventListener('change', (event) => { state.sort = event.target.value; render(); });
els.refreshBtn.addEventListener('click', () => loadTokens({ force: true }));

loadTokens();
setInterval(() => loadTokens(), 60_000);
