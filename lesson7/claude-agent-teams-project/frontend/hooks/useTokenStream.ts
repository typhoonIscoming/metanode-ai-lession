"use client";

// 订阅后端快照数据流的 React hook
// 1. mount 时先调 REST `/api/tokens` 拿初始快照（首次抓取未完成时后端返回 503，会被记为 error 但 EventSource 仍会接管）
// 2. 建立 EventSource 监听 `/api/stream` 的 `snapshot` 事件
// 3. 对比新旧快照，为每个 symbol 生成 300ms 的 flash 高亮状态（涨 → "up"，跌 → "down"）
// 4. 组件卸载时关闭 EventSource，并清理所有 flash 定时器

import { useEffect, useRef, useState } from "react";

import type { SnapshotResponse, TokenSnapshot } from "@/types/snapshot";

/** flash 高亮持续时长（毫秒），与设计稿一致 */
const FLASH_DURATION_MS = 300;

/** flash 方向：上涨 / 下跌；无变化或新增不闪 */
export type FlashDirection = "up" | "down";

/** hook 返回值 */
export interface UseTokenStreamResult {
  /** 最新快照；尚未拿到时为 null */
  snapshot: SnapshotResponse | null;
  /** 初始 REST 加载是否在途 */
  loading: boolean;
  /** 最近一次错误的简短描述；恢复后可被新的成功事件覆盖 */
  error: string | null;
  /** 每个 symbol 对应的 flash 方向（300ms 内有效），UI 可据此做高亮动画 */
  flashMap: Record<string, FlashDirection>;
}

/** 读取 NEXT_PUBLIC_API_BASE，去除末尾斜杠避免出现 `//api/tokens` */
function getApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

/** 把 token 列表按 symbol 建索引，便于 O(1) 对比价格 */
function indexBySymbol(tokens: TokenSnapshot[]): Map<string, TokenSnapshot> {
  const map = new Map<string, TokenSnapshot>();
  for (const t of tokens) {
    map.set(t.symbol, t);
  }
  return map;
}

/** 对比新旧快照，返回需要触发 flash 的 symbol -> direction 映射 */
function diffFlash(
  prev: SnapshotResponse | null,
  next: SnapshotResponse,
): Record<string, FlashDirection> {
  if (!prev) return {};
  const prevIdx = indexBySymbol(prev.tokens);
  const out: Record<string, FlashDirection> = {};
  for (const t of next.tokens) {
    const old = prevIdx.get(t.symbol);
    if (!old) continue;
    if (t.price > old.price) {
      out[t.symbol] = "up";
    } else if (t.price < old.price) {
      out[t.symbol] = "down";
    }
  }
  return out;
}

export function useTokenStream(): UseTokenStreamResult {
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [flashMap, setFlashMap] = useState<Record<string, FlashDirection>>({});

  // 用 ref 保存「最新一份 snapshot」，避免 SSE 回调闭包捕获到旧 state
  const latestRef = useRef<SnapshotResponse | null>(null);
  // 每个 symbol 对应的 flash 清理定时器，方便覆盖与卸载时统一清理
  const flashTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  useEffect(() => {
    const apiBase = getApiBase();
    // 标记本 effect 是否已被卸载，避免在卸载后还调用 setState
    let cancelled = false;

    /** 应用一份新快照：更新 state + 触发 flash + 安排清理 */
    const applySnapshot = (next: SnapshotResponse) => {
      if (cancelled) return;
      const flashes = diffFlash(latestRef.current, next);
      latestRef.current = next;
      setSnapshot(next);

      if (Object.keys(flashes).length > 0) {
        setFlashMap((current) => ({ ...current, ...flashes }));
        for (const symbol of Object.keys(flashes)) {
          // 同一 symbol 若已有未到期的定时器，先取消，再覆盖
          const prevTimer = flashTimersRef.current.get(symbol);
          if (prevTimer) clearTimeout(prevTimer);
          const timer = setTimeout(() => {
            flashTimersRef.current.delete(symbol);
            setFlashMap((current) => {
              if (!(symbol in current)) return current;
              const next = { ...current };
              delete next[symbol];
              return next;
            });
          }, FLASH_DURATION_MS);
          flashTimersRef.current.set(symbol, timer);
        }
      }
    };

    // 第 1 步：拉初始快照
    (async () => {
      try {
        const res = await fetch(`${apiBase}/api/tokens`, {
          headers: { Accept: "application/json" },
          cache: "no-store",
        });
        if (!res.ok) {
          // 503 表示首次抓取未完成，并不致命 —— EventSource 接管后第一帧也能补上
          throw new Error(`GET /api/tokens 返回 ${res.status}`);
        }
        const data = (await res.json()) as SnapshotResponse;
        applySnapshot(data);
        if (!cancelled) setError(null);
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          console.warn("[useTokenStream] 初始快照加载失败：", msg);
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    // 第 2 步：建立 SSE 订阅
    const es = new EventSource(`${apiBase}/api/stream`);

    es.addEventListener("snapshot", (ev) => {
      try {
        const data = JSON.parse((ev as MessageEvent<string>).data) as SnapshotResponse;
        applySnapshot(data);
        if (!cancelled) setError(null);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        console.warn("[useTokenStream] 解析 snapshot 事件失败：", msg);
        if (!cancelled) setError(`解析 SSE 事件失败：${msg}`);
      }
    });

    es.onerror = () => {
      // EventSource 会自动重连，这里只记录日志和暴露错误状态，不主动关闭
      console.warn("[useTokenStream] SSE 连接异常，等待浏览器自动重连");
      if (!cancelled) setError("SSE 连接异常，已触发自动重连");
    };

    // 卸载清理：关 SSE + 清空所有 flash 定时器
    // 把 ref 当前值拷到局部变量，规避 react-hooks/exhaustive-deps 的常见告警
    const timersAtSetup = flashTimersRef.current;
    return () => {
      cancelled = true;
      es.close();
      for (const timer of timersAtSetup.values()) {
        clearTimeout(timer);
      }
      timersAtSetup.clear();
    };
  }, []);

  return { snapshot, loading, error, flashMap };
}
