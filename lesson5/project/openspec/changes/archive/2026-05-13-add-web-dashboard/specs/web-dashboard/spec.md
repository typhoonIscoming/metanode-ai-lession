## ADDED Requirements

### Requirement: Single-page strategy dashboard

The `web-dashboard` capability SHALL serve a single HTML page at `GET /` that lists every registered strategy and exposes a form to configure and trigger a backtest. The page MUST work without any frontend build step (no npm / webpack).

#### Scenario: Landing page renders strategy list

- **WHEN** a user opens `http://localhost:5000/` in a modern browser
- **THEN** the page renders without errors and shows a `<select>` (or equivalent) listing every strategy registered in the backend (at minimum: `dual_ma`, `rsi_reversal`, `buy_and_hold`)

#### Scenario: Form exposes symbol and history length

- **WHEN** the dashboard form is rendered
- **THEN** the form MUST allow the user to choose at least:
  - a strategy (from the registered list)
  - a symbol (at minimum `BTCUSDT` and `ETHUSDT`)
  - a K-line count (`limit`), with a sensible default and a sane upper bound

### Requirement: Backtest endpoint reuses existing engine

The dashboard SHALL invoke `backtest.run_backtest()` from `project/backtest.py` **without modification** to that module. The backend MUST NOT re-implement metric calculation, PNG rendering, or summary generation — those are owned by the existing engine.

#### Scenario: Backend forwards parameters to run_backtest

- **WHEN** the frontend submits a form to the backtest endpoint with `(strategy_name, symbol, limit)`
- **THEN** the backend resolves `strategy_name` to a callable from a strategy registry and calls `run_backtest(callable, symbol=..., limit=...)`, returning the engine's result dict (sharpe, max_drawdown, win_rate, cumulative_return, png_path, summary, rows) verbatim

#### Scenario: Strategy modules are untouched

- **WHEN** a reviewer diffs `project/strategies/*.py` and `project/backtest.py` before vs after this change
- **THEN** none of those files have been modified

### Requirement: Result rendering

After a backtest completes, the dashboard MUST display the four headline metrics, the Chinese summary, and the cumulative-return PNG on the same page. The user MUST NOT need to refresh manually.

#### Scenario: Successful backtest shows metrics

- **WHEN** the user clicks "Run backtest" and the backend returns a result
- **THEN** the page displays `sharpe`, `max_drawdown`, `win_rate`, `cumulative_return` as formatted numbers (percentages where appropriate), and the Chinese `summary` text

#### Scenario: PNG is displayed inline

- **WHEN** a result includes a `png_path`
- **THEN** the page renders that PNG as an `<img>` element so the user does not need to open the file manually

#### Scenario: Latest result replaces prior result

- **WHEN** the user runs a second backtest in the same session without refreshing
- **THEN** the new metrics and chart replace the old ones on the same page; no stale data is shown

### Requirement: Error handling

The dashboard MUST surface backend errors to the user instead of failing silently.

#### Scenario: Unknown strategy

- **WHEN** the frontend submits a `strategy_name` not present in the registry
- **THEN** the backend returns an HTTP 4xx with a JSON body containing a human-readable error message, and the frontend displays it (e.g., red banner)

#### Scenario: Empty database

- **WHEN** `prices.db` does not contain the requested symbol
- **THEN** the backend catches the engine's `ValueError`, returns HTTP 4xx with the original error message ("先跑 python seed_db.py")

### Requirement: Self-contained folder layout

All web artifacts SHALL live under `project/web/`. The dashboard MUST NOT add files outside that directory except for:
- a single line appended to the project-root `.gitignore`
- the `web/static/results/` directory used for generated PNGs (gitignored content, `.gitkeep` tracked)

#### Scenario: Tree audit

- **WHEN** a reviewer lists the project tree before vs after this change
- **THEN** new files only appear under `project/web/`, and the only file modified outside `web/` is `.gitignore`

### Requirement: Minimal external dependencies

The backend MUST add exactly one new Python dependency (Flask) recorded in `web/requirements.txt`. No new system-level or build-time dependencies (no Node, no SCSS preprocessor, no asset bundler).

#### Scenario: Install footprint check

- **WHEN** a user follows `web/README.md` to set up
- **THEN** the only `pip install` line they need is `pip install -r web/requirements.txt`, and that file lists only flask (and any transitive deps pip resolves)

### Requirement: Local-development run command

`web/README.md` MUST document a single command that starts the server, and that command MUST work from the `project/` directory.

#### Scenario: One-command launch from project root

- **WHEN** a user runs the documented command from `project/`
- **THEN** the Flask server starts on a default port (5000) and prints the URL; opening that URL renders the dashboard

### Requirement: UTC + Chinese-comments conventions inherited

The web module MUST honour the two project-wide conventions: all time handling in UTC; all code comments and docstrings in Chinese (English identifiers).

#### Scenario: Audit web/app.py

- **WHEN** a reviewer reads `web/app.py`
- **THEN** no naive `datetime.now()` / `datetime.fromtimestamp(x)` appears; module docstrings and inline comments are in Chinese

### Requirement: PNG output isolation

PNGs produced by dashboard-triggered backtests MUST be written to `web/static/results/`. They MUST NOT be written into the project root (which is where the CLI `backtest.py` defaults to) so the two surfaces don't collide on the same `cum_<symbol>.png` filename.

#### Scenario: PNG path is under web/static/results/

- **WHEN** a dashboard backtest produces a chart
- **THEN** `result["png_path"]` resolves to a file under `project/web/static/results/`, and `project/cum_BTCUSDT.png` (CLI output) is not overwritten

#### Scenario: Filename de-collides across runs

- **WHEN** the user runs two backtests with the same `(strategy, symbol)`
- **THEN** both PNGs are kept (e.g., timestamp-suffixed) OR the second overwrites the first deterministically — the design MUST choose one behaviour and document it
