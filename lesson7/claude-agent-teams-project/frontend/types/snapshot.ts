// 后端快照数据契约的 TypeScript 类型定义
// 字段与 backend/app/models.py 中的 Pydantic 模型严格一致
// 所有时间字段统一使用 UTC 毫秒 epoch 时间戳（number）

/** 单个交易对的快照数据 */
export interface TokenSnapshot {
  /** 交易对名称，如 BTCUSDT */
  symbol: string;
  /** 基础资产代码，如 BTC（symbol 去掉末尾 USDT 得到），UI 色块直接显示 */
  baseAsset: string;
  /** 当前最新价（USDT 计价） */
  price: number;
  /** 24h 计价货币成交量（USDT），用于排序和热力图色块大小 */
  quoteVolume: number;
  /** Binance 提供的 24h 涨跌幅（百分数，如 1.23 表示 +1.23%） */
  priceChangePercent: number;
  /** 相邻两次抓取之间的价格变化率（小数，如 0.001 表示 +0.1%），首次抓取为 null */
  priceChangeRate: number | null;
}

/** 一次完整抓取的快照响应 */
export interface SnapshotResponse {
  /** 本次抓取完成时间，UTC 毫秒 epoch */
  fetchedAt: number;
  /** 上一次抓取完成时间，UTC 毫秒 epoch；首次为 null */
  previousFetchedAt: number | null;
  /** 按 24h 成交量降序排列的交易对快照列表（通常前 100） */
  tokens: TokenSnapshot[];
}
