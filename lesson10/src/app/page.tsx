"use client";

import { useMemo, useState } from 'react';

type Result = any;

const goals = [
  { value: 'stable_growth', label: '稳健收益' },
  { value: 'capture_trend', label: '捕捉趋势' },
  { value: 'control_drawdown', label: '控制回撤' },
];

export default function Home() {
  const [symbol, setSymbol] = useState('BTC');
  const [riskProfile, setRiskProfile] = useState('balanced');
  const [goal, setGoal] = useState('capture_trend');
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function run() {
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/run-strategy', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, riskProfile, goal }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || '运行失败');
      setResult(data);
    } catch (e: any) {
      setError(e.message || '运行失败');
    } finally { setLoading(false); }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">Hyperliquid Lesson 10 · Demo Mode</div>
          <h1>AI Strategy Cockpit</h1>
          <p>基于 Hyperliquid 真实历史 K 线，由 LLM 在趋势、RSI、布林带策略中做专业判断。</p>
        </div>
        <div className="badges"><span>Hyperliquid Historical Data</span><span>LLM Strategy Advisor</span><span>Simulation Only</span></div>
      </header>

      <section className="controls card">
        <Select label="Symbol" value={symbol} setValue={setSymbol} options={[['BTC','BTC'],['ETH','ETH'],['SOL','SOL']]} />
        <Select label="Risk Profile" value={riskProfile} setValue={setRiskProfile} options={[["conservative","保守"],["balanced","均衡"],["aggressive","激进"]]} />
        <Select label="Goal" value={goal} setValue={setGoal} options={goals.map(g=>[g.value,g.label])} />
        <button className="run" onClick={run} disabled={loading}>{loading ? 'Running...' : 'Run AI Strategy'}</button>
      </section>

      {error && <div className="error">{error}</div>}
      {loading && <LoadingPanel />}
      {!loading && !result && <IdlePanel />}
      {result && !loading && <Cockpit result={result} />}

      <footer className="disclaimer">本演示仅用于教学和模拟，不执行真实交易，不构成投资建议。</footer>
    </main>
  );
}

function Select({ label, value, setValue, options }: any) {
  return <label className="field"><span>{label}</span><select value={value} onChange={(e)=>setValue(e.target.value)}>{options.map(([v,l]: any)=><option key={v} value={v}>{l}</option>)}</select></label>;
}

function LoadingPanel() {
  const steps = ['Reading Hyperliquid historical candles...', 'Calculating MA / RSI / Bollinger indicators...', 'Asking LLM to choose a strategy...', 'Running deterministic backtest...', 'Rendering cockpit...'];
  return <section className="card loading">{steps.map((s,i)=><div key={s} style={{animationDelay:`${i*120}ms`}}>{s}</div>)}</section>;
}

function IdlePanel() {
  return <section className="card idle-panel">
    <h2>等待运行策略</h2>
    <p>点击 Run AI Strategy 后，系统会读取 Hyperliquid 历史 K 线，计算 MA / RSI / 布林带指标，并让 LLM 选择最合适的策略再执行模拟回测。</p>
  </section>;
}

function Cockpit({ result }: { result: Result }) {
  return <>
    <section className="grid">
      <div className="card chart-card"><h2>Equity Curve</h2><EquityChart result={result} /></div>
      <AIAnalysis result={result} />
    </section>
    <section className="metrics">
      <Metric title="Total Return" value={pct(result.metrics.totalReturn)} positive={result.metrics.totalReturn >= 0} />
      <Metric title="Max Drawdown" value={pct(result.metrics.maxDrawdown)} />
      <Metric title="Win Rate" value={pct(result.metrics.winRate)} positive />
      <Metric title="Trades" value={String(result.metrics.tradeCount)} />
      <Metric title="Final Equity" value={`$${result.metrics.finalEquity.toLocaleString()}`} positive />
    </section>
    <section className="grid bottom">
      <StrategyCard result={result} />
      <TradeLog trades={result.trades} />
    </section>
  </>;
}

function EquityChart({ result }: { result: Result }) {
  const points = useMemo(() => {
    const curve = result.chart.equityCurve || [];
    const min = Math.min(...curve.map((p:any)=>p.equity));
    const max = Math.max(...curve.map((p:any)=>p.equity));
    const span = Math.max(max - min, 1);
    return curve.map((p:any, i:number) => {
      const x = (i / Math.max(curve.length - 1, 1)) * 1000;
      const y = 280 - ((p.equity - min) / span) * 240;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }, [result]);
  return <div className="svg-wrap"><svg viewBox="0 0 1000 320" role="img" aria-label="equity curve"><defs><linearGradient id="line" x1="0" x2="1"><stop stopColor="#7c3aed"/><stop offset="1" stopColor="#22c55e"/></linearGradient></defs><polyline points={points} fill="none" stroke="url(#line)" strokeWidth="5" strokeLinecap="round"/><line x1="0" y1="280" x2="1000" y2="280" stroke="#1e293b"/><text x="18" y="34" fill="#94a3b8">{result.dataSource} · {result.aiAnalysis.source}</text></svg></div>;
}

function AIAnalysis({ result }: { result: Result }) {
  const a = result.aiAnalysis;
  return <aside className="card ai"><h2>AI Analysis</h2><Tag>{a.source === 'llm' ? 'Real LLM Judgment' : 'Fallback Rules'}</Tag><Tag>{a.marketRegime}</Tag><h3>Market Regime</h3><p>{a.summary}</p><h3>Opportunity</h3><p>{a.opportunity}</p><h3>Risk</h3><p>{a.risk}</p><h3>Why This Strategy</h3><p>{a.strategyReason}</p></aside>;
}

function StrategyCard({ result }: { result: Result }) {
  const params = result.strategy.parameters;
  return <section className="card selected-strategy-card">
    <div className="selection-kicker">AI 最终选择的策略</div>
    <h2>Selected Strategy</h2>
    <div className="strategy-name">{result.strategy.name}</div>
    <div className="strategy-meta">
      <span>Strategy ID: {result.strategy.id}</span>
      <span>AI Selection Source: {result.aiAnalysis.source === 'llm' ? 'gpt-5.5 LLM' : 'fallback rules'}</span>
    </div>
    <p>{strategyDescription(result.strategy.id)}</p>
    <p>{result.aiAnalysis.strategyReason}</p>
    <div className="param-grid">{Object.entries(params).map(([k,v])=><div key={k}><span>{k}</span><b>{typeof v === 'number' && v < 1 ? pct(v) : String(v)}</b></div>)}</div>
  </section>;
}

function TradeLog({ trades }: { trades: any[] }) {
  return <section className="card"><h2>Simulation Timeline</h2><div className="table">{trades.map((t)=> <div className="row" key={`${t.timestamp}-${t.action}-${t.price}`}><span>{t.timestamp}</span><b className={t.action === 'BUY' ? 'buy' : 'sell'}>{t.action}</b><span>${t.price}</span><span>{t.reason}</span></div>)}</div></section>;
}

function Metric({ title, value, positive }: any) { return <div className="metric card"><span>{title}</span><strong className={positive ? 'positive' : ''}>{value}</strong></div>; }
function Tag({ children }: any) { return <span className="tag">{children}</span>; }
function pct(v: number) { return `${(v * 100).toFixed(1)}%`; }
function strategyDescription(id: string) {
  if (id === 'trend_following') return '趋势跟随：用快慢均线判断主趋势方向，适合趋势明确的行情。';
  if (id === 'rsi_mean_reversion') return 'RSI 均值回归：用 RSI 判断超买/超卖，适合震荡和回撤控制场景。';
  if (id === 'bollinger_bands') return '布林带策略：用价格相对上下轨的位置判断波动突破或均值回归机会。';
  return 'AI 选择的专业策略。';
}
