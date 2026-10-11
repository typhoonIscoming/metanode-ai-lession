"use client";

// 加密货币市值热力图（Finviz / Coin360 风格）
// - 色块面积 ∝ token.quoteVolume（后端用 24h 成交额作为市值代理）
// - 颜色按 priceChangeRate 渐变：正绿、负红、null 灰
// - 顶部 header 展示标题 / UTC 最后更新时间 / 数据来源说明
// - 收到新快照时通过 hook 的 flashMap 做 300ms 外环高亮

import { useEffect, useMemo, useRef, useState } from "react";
import {
  hierarchy,
  treemap,
  treemapSquarify,
  type HierarchyRectangularNode,
} from "d3-hierarchy";

import { useTokenStream, type FlashDirection } from "@/hooks/useTokenStream";
import type { TokenSnapshot } from "@/types/snapshot";

/** treemap 渲染区域的尺寸（像素） */
interface BoxSize {
  width: number;
  height: number;
}

/** 单个 treemap 叶子节点渲染所需的数据 */
interface LeafNode {
  token: TokenSnapshot;
  x: number;
  y: number;
  width: number;
  height: number;
}

/** 颜色映射：把 priceChangeRate（小数）→ Tailwind 背景色 class */
function colorForRate(rate: number | null): string {
  if (rate === null || Number.isNaN(rate)) return "bg-zinc-600";
  // 以 ±5% 为饱和上限分桶；rate 是小数（0.01 = 1%）
  const abs = Math.min(Math.abs(rate), 0.05);
  if (rate > 0) {
    if (abs < 0.005) return "bg-emerald-900";
    if (abs < 0.01) return "bg-emerald-800";
    if (abs < 0.02) return "bg-emerald-700";
    if (abs < 0.03) return "bg-emerald-600";
    return "bg-emerald-500";
  }
  if (rate < 0) {
    if (abs < 0.005) return "bg-rose-900";
    if (abs < 0.01) return "bg-rose-800";
    if (abs < 0.02) return "bg-rose-700";
    if (abs < 0.03) return "bg-rose-600";
    return "bg-rose-500";
  }
  return "bg-zinc-700";
}

/** flash 方向 → 短暂高亮的外环 Tailwind class */
function ringForFlash(direction: FlashDirection | undefined): string {
  if (direction === "up") return "ring-2 ring-emerald-300";
  if (direction === "down") return "ring-2 ring-rose-300";
  return "";
}

/** 色块上显示的简短代码：优先用后端给的 baseAsset，缺失时回退从 symbol 截 USDT */
function displayBase(token: TokenSnapshot): string {
  if (token.baseAsset) return token.baseAsset;
  return token.symbol.endsWith("USDT")
    ? token.symbol.slice(0, -4)
    : token.symbol;
}

/** 价格格式化：高价用千分位整数，低价保留更多小数 */
function formatPrice(price: number): string {
  if (price >= 1000) {
    return `$${price.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  }
  if (price >= 1) {
    return `$${price.toFixed(2)}`;
  }
  if (price >= 0.01) {
    return `$${price.toFixed(4)}`;
  }
  return `$${price.toPrecision(4)}`;
}

/** 变化率格式化：用 priceChangePercent（已经是百分数），保留 2 位小数 */
function formatChangePercent(percent: number): string {
  // U+2212 是真正的减号，比 ASCII '-' 更对齐
  const sign = percent > 0 ? "+" : percent < 0 ? "−" : "";
  return `${sign}${Math.abs(percent).toFixed(2)}%`;
}

/** 把 ms epoch 时间戳格式化为 UTC ISO 字符串（带 Z 后缀） */
function formatUtc(ms: number): string {
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
}

/** 监听元素尺寸变化的 hook，treemap 需要实际宽高才能布局 */
function useElementSize<T extends HTMLElement>(): [
  React.RefObject<T | null>,
  BoxSize,
] {
  const ref = useRef<T | null>(null);
  const [size, setSize] = useState<BoxSize>({ width: 0, height: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setSize({ width, height });
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, size];
}

/** 根据色块尺寸自适应字号；过小则隐藏文本 */
function pickFontSizes(width: number, height: number): {
  symbol: number;
  price: number;
  change: number;
  showPrice: boolean;
  showChange: boolean;
} {
  const min = Math.min(width, height);
  const symbol = Math.max(10, Math.min(36, min * 0.22));
  const price = Math.max(9, Math.min(16, min * 0.11));
  const change = Math.max(9, Math.min(14, min * 0.1));
  return {
    symbol,
    price,
    change,
    showPrice: width >= 60 && height >= 50,
    showChange: width >= 50 && height >= 40,
  };
}

/** d3-hierarchy 输入节点类型 */
interface TreeNode {
  children?: TreeNode[];
  token?: TokenSnapshot;
}

export default function Home() {
  const { snapshot, loading, error, flashMap } = useTokenStream();
  const [boxRef, size] = useElementSize<HTMLDivElement>();

  // 计算 treemap 布局：仅在快照 / 容器尺寸变化时重新计算
  const leaves = useMemo<LeafNode[]>(() => {
    if (!snapshot || size.width <= 0 || size.height <= 0) return [];
    const tokens = snapshot.tokens.filter((t) => t.quoteVolume > 0);
    if (tokens.length === 0) return [];

    // d3 hierarchy 期望树形结构，包一层 root，叶子节点的 value 取 quoteVolume
    const root = hierarchy<TreeNode>(
      { children: tokens.map((t) => ({ token: t })) },
      (d) => d.children,
    ).sum((d) => (d.token ? d.token.quoteVolume : 0));

    // treemap layout 会就地为 root 及其所有子孙节点写入 x0/y0/x1/y1，
    // 因此返回值（含 root）实际类型是 HierarchyRectangularNode
    const layout = treemap<TreeNode>()
      .size([size.width, size.height])
      .paddingInner(2)
      .round(true)
      .tile(treemapSquarify);
    const rectRoot = layout(root) as HierarchyRectangularNode<TreeNode>;

    return rectRoot
      .leaves()
      .map((leaf) => {
        const t = leaf.data.token;
        if (!t) return null;
        return {
          token: t,
          x: leaf.x0,
          y: leaf.y0,
          width: leaf.x1 - leaf.x0,
          height: leaf.y1 - leaf.y0,
        } satisfies LeafNode;
      })
      .filter((n): n is LeafNode => n !== null);
  }, [snapshot, size]);

  const lastUpdate = snapshot ? formatUtc(snapshot.fetchedAt) : "—";

  return (
    <main className="flex flex-1 flex-col bg-zinc-950 text-zinc-100">
      <header className="flex flex-col gap-1 border-b border-zinc-800 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col">
          <h1 className="text-lg font-semibold tracking-tight">
            Crypto Market Heatmap
          </h1>
          <p className="text-xs text-zinc-400">
            Binance 24h quoteVolume as market cap proxy
          </p>
        </div>
        <div className="flex flex-col items-start sm:items-end">
          <span className="text-xs text-zinc-400">Last update (UTC)</span>
          <span className="font-mono text-sm tabular-nums text-zinc-200">
            {lastUpdate}
          </span>
          {error && (
            <span className="mt-1 text-xs text-amber-400">{error}</span>
          )}
        </div>
      </header>

      <div ref={boxRef} className="relative flex-1 overflow-hidden">
        {/* 加载 / 空数据状态 */}
        {loading && leaves.length === 0 && (
          <div className="flex h-full w-full items-center justify-center text-sm text-zinc-400">
            Loading…
          </div>
        )}
        {!loading && leaves.length === 0 && (
          <div className="flex h-full w-full items-center justify-center text-sm text-zinc-400">
            暂无数据
          </div>
        )}

        {/* 色块渲染：用绝对定位 + d3 计算的坐标，transition 让 SSE 更新时尺寸位置平滑过渡 */}
        {leaves.map(({ token, x, y, width, height }) => {
          const fonts = pickFontSizes(width, height);
          const flash = flashMap[token.symbol];
          return (
            <div
              key={token.symbol}
              className={[
                "absolute flex flex-col items-center justify-center overflow-hidden",
                "rounded-sm transition-all duration-300 ease-out",
                colorForRate(token.priceChangeRate),
                ringForFlash(flash),
              ].join(" ")}
              style={{
                left: x,
                top: y,
                width,
                height,
              }}
              title={`${token.symbol} · 24h vol $${token.quoteVolume.toLocaleString("en-US", { maximumFractionDigits: 0 })}`}
            >
              <span
                className="font-semibold leading-none text-white drop-shadow-sm"
                style={{ fontSize: `${fonts.symbol}px` }}
              >
                {displayBase(token)}
              </span>
              {fonts.showPrice && (
                <span
                  className="mt-1 font-mono tabular-nums text-white/90"
                  style={{ fontSize: `${fonts.price}px` }}
                >
                  {formatPrice(token.price)}
                </span>
              )}
              {fonts.showChange && (
                <span
                  className="font-mono tabular-nums text-white/80"
                  style={{ fontSize: `${fonts.change}px` }}
                >
                  {formatChangePercent(token.priceChangePercent)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
