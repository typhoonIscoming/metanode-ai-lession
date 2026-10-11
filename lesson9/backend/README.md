# btc-arb backend

Polymarket BTC 套利信号工具后端，详见 `../backend-PRD.md`。

## 本地开发

```bash
# 安装依赖（含 dev）
pip install -e ".[dev]"

# 拷贝环境变量
cp .env.example .env

# 起一个 Postgres（推荐 docker）
docker run -d --name btc-arb-db \
  -e POSTGRES_USER=btc_arb -e POSTGRES_PASSWORD=btc_arb -e POSTGRES_DB=btc_arb \
  -p 127.0.0.1:5432:5432 postgres:16

# 跑迁移
alembic upgrade head

# 启动
uvicorn btc_arb.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

- 健康检查：`http://127.0.0.1:8000/api/v1/healthz`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`

## 单测 / lint

```bash
pytest
ruff check .
```

## 风险声明

本工具仅作个人研究信号提醒，不构成投资建议。
