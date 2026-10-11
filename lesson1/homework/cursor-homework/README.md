# crypto_monitor — 加密货币行情监控 CLI

Lesson 1 课后作业（Cursor 版）。一个单文件 Python CLI，用 Binance 公开接口拉取 BTC/ETH 等币种实时价格，落库到本地 SQLite，并支持阈值告警和统计查询。

## 功能一览

| 子命令 | 用途 |
| ------ | ---- |
| `price`  | 一次性查询若干币种当前价格并落库 |
| `watch`  | 周期性轮询、打印并落库，`Ctrl+C` 退出 |
| `alert`  | 周期性轮询单币种，跨越阈值时打印告警 |
| `stats`  | 从 SQLite 查询某币种最近 N 条的最高 / 最低 / 均价 |

支持币种：`BTC`、`ETH`、`SOL`、`BNB`（在脚本顶部 `SYMBOL_MAP` 中扩展即可）。

## 安装

```bash
pip install -r requirements.txt
```

## 用法

```bash
# 1) 一次查询
python crypto_monitor.py price BTC ETH

# 2) 周期轮询（默认 10 秒一次，0 表示一直跑到 Ctrl+C）
python crypto_monitor.py watch BTC ETH --interval 5
python crypto_monitor.py watch BTC --interval 5 --duration 60

# 3) 阈值告警（--above / --below 至少给一个）
python crypto_monitor.py alert BTC --above 70000 --below 60000 --interval 30

# 4) 统计最近 N 条（默认 100）
python crypto_monitor.py stats BTC --last 50

# 自定义数据库路径
python crypto_monitor.py --db /tmp/my.db price BTC
```

## 数据存储

- 默认数据库：与脚本同目录的 `prices.db`，用 `--db` 可覆盖。
- 表结构：

  ```sql
  CREATE TABLE prices (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT    NOT NULL,
    price  REAL    NOT NULL,
    ts     TEXT    NOT NULL  -- ISO 8601 UTC, 例如 2026-04-19T08:30:00+00:00
  );
  ```

## 时间约定

整个仓库统一使用 **UTC**：脚本生成时间一律 `datetime.now(timezone.utc)`，落库 / 打印都带 `+00:00` 后缀，避免因机器时区不同导致数据错位。详见仓库根的 `.cursor/rules/project-conventions.mdc`。

## 数据源

Binance 现货 ticker 接口：

```
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

无需 API key。如果在被墙的网络环境运行，请自行解决出口问题（脚本不内置代理逻辑）。
