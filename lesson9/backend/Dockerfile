FROM python:3.12-slim

WORKDIR /app

# curl 给 healthcheck 用；其余构建依赖按需添加
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖，便于利用 Docker 层缓存
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# 拷剩余文件
COPY alembic.ini ./
COPY alembic ./alembic

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn btc_arb.main:app --host 0.0.0.0 --port 8000"]
