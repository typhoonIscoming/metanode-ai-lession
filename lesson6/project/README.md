# quant-trader

一个跑在 Binance Testnet 上的小型量化交易系统：写策略 → 回测 → 实时纸交易 / testnet 模拟下单 → Web 看板看持仓与 P&L。

## Quick start

```bash
pip install -e ".[dev]"
cp .env.example .env  # 填上你的 Binance Testnet API key/secret（可选）
python scripts/seed_db.py
uvicorn app.main:app --reload
# 打开 http://localhost:8000
```

## 项目结构

详见 `docs/superpowers/specs/2026-05-17-quant-trader-v1-design.md` §4。

## 命令

- `pytest --cov=app --cov-fail-under=80`  跑测试
- `ruff check .`  lint
- `uvicorn app.main:app --reload`  起服务

## 设计

- spec: `docs/superpowers/specs/2026-05-17-quant-trader-v1-design.md`
- plan: `docs/superpowers/plans/2026-05-17-quant-trader-v1.md`
