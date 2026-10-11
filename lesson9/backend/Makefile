.PHONY: help install lint test test-unit test-cov test-cov-strict test-contract clean

PYTHON ?= python
PYTEST ?= pytest
COV_PKG = src/btc_arb

help:
	@echo "可用目标："
	@echo "  install            安装 dev 依赖（含 pytest/coverage/testcontainers）"
	@echo "  lint               ruff 静态检查"
	@echo "  test               跑 unit + integration（不收集覆盖率，快速反馈）"
	@echo "  test-unit          仅跑 unit"
	@echo "  test-cov           跑 unit + integration + 整体 >= 80% 硬卡"
	@echo "  test-cov-strict    在 test-cov 基础上跑分级门禁（critical 95% / business 85%）"
	@echo "  test-contract      跑契约测试（不计入覆盖率）"
	@echo "  clean              清理覆盖率与 cache"

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	$(PYTEST) tests/unit tests/integration -m "not contract"

test-unit:
	$(PYTEST) tests/unit -m "not contract"

test-cov:
	$(PYTEST) tests/unit tests/integration \
		-m "not contract" \
		--cov=$(COV_PKG) \
		--cov-report=term-missing \
		--cov-report=json \
		--cov-report=html \
		--no-cov-on-fail

# 合并门禁：80% 整体 + per-file 95/85。pre-merge / CI 用。
test-cov-strict:
	$(PYTEST) tests/unit tests/integration \
		-m "not contract" \
		--cov=$(COV_PKG) \
		--cov-report=term-missing \
		--cov-report=json \
		--cov-report=html \
		--cov-fail-under=80 \
		--no-cov-on-fail
	$(PYTHON) scripts/check_coverage.py

test-contract:
	$(PYTEST) tests/contract -m contract --no-cov

clean:
	rm -rf .coverage coverage.json coverage.xml htmlcov .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
