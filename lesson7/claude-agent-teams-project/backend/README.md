# Crypto Heatmap Backend

加密货币市值热力图后端服务，基于 FastAPI + APScheduler + SSE。
抓取 Binance 24h 行情，每 30s 推送一次快照给前端。

## 前置依赖

- Python 3.11+
- 网络可访问 `api.binance.com`

## 安装

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 启动

```bash
uvicorn app.main:app --reload --port 8000
```

默认监听 `http://localhost:8000`。

## 接口一览

| 方法 | 路径          | 说明                                                                |
| ---- | ------------- | ------------------------------------------------------------------- |
| GET  | `/api/health` | 健康检查，返回 `{"status":"ok"}`                                    |
| GET  | `/api/tokens` | 返回最新一次抓取的 `SnapshotResponse`；首抓未完成时返回 503         |
| GET  | `/api/stream` | SSE 长连接，event 名 `snapshot`，data 为 `SnapshotResponse` JSON    |

## 运行机制

- 启动时调度器立即跑一次首抓，之后每 30 秒抓取一次
- 抓取结果写入内存最新缓存（供 `/api/tokens` 读取），并广播到所有 SSE 订阅者
- SSE 新连接建立时会立即推送当前最新缓存，无需等待下一轮调度
- 抓取异常会记录日志但不会中断调度器，下一轮继续

## 手动验证

```bash
# 健康检查
curl http://localhost:8000/api/health
# {"status":"ok"}

# 等几秒首抓完成后看快照
curl http://localhost:8000/api/tokens | jq '.tokens | length'
# 100

# 订阅 SSE，持续看到 event: snapshot
curl -N http://localhost:8000/api/stream
```

## 项目约定

- 所有时间使用 UTC 毫秒 epoch（`int(time.time() * 1000)`）
- 代码注释与 docstring 统一使用中文
- CORS 仅放行 `http://localhost:3000`（前端开发地址）

## 数据契约

见 `app/models.py`：

```ts
TokenSnapshot {
  symbol: string                  // "BTCUSDT"
  baseAsset: string               // "BTC"（去掉末尾 USDT，前端 UI 显示用）
  price: number                   // 当前最新价（USDT）
  quoteVolume: number             // 24h USDT 成交额，用于排序与色块大小
  priceChangeRate: number | null  // 相对上次抓取的变化率，首次为 null
  priceChangePercent: number      // Binance 24h 涨跌幅（百分数）
}

SnapshotResponse {
  fetchedAt: number               // UTC 毫秒 epoch
  previousFetchedAt: number | null
  tokens: TokenSnapshot[]         // 按 quoteVolume 降序，最多 100 个
}
```
