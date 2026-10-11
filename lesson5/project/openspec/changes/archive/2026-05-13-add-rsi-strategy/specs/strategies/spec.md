## ADDED Requirements

### Requirement: RSI reversal strategy callable

The `strategies` package SHALL expose a callable `rsi_reversal(df, period=14, oversold=30, overbought=70) -> pd.Series`. The returned Series MUST be indexed identically to `df.index` and MUST contain only values from `{0, +1}` (long-only). The callable MUST be importable both as `strategies.rsi_reversal` (top-level re-export) and as `strategies.rsi_reversal.rsi_reversal` (module-level).

#### Scenario: Function is exposed at package top level

- **WHEN** user code runs `from strategies import rsi_reversal`
- **THEN** the import succeeds and `rsi_reversal` is callable

#### Scenario: Signature accepts the documented keyword arguments

- **WHEN** user code calls `rsi_reversal(df, period=14, oversold=30, overbought=70)`
- **THEN** the call returns a `pd.Series` with the same index as `df` and only `{0, +1}` values

#### Scenario: Compatible with `run_backtest`

- **WHEN** `backtest.run_backtest(rsi_reversal)` is invoked on a `prices.db` containing at least `period + 2` rows
- **THEN** the call returns a result dict containing the keys `sharpe`, `max_drawdown`, `win_rate`, `cumulative_return`, `png_path`, `summary`, `rows` without raising

### Requirement: RSI crossing-based entry and exit

The strategy SHALL enter long (emit `+1`) when the RSI rises **through** the `oversold` threshold from below, and SHALL exit to flat (emit `0`) when the RSI falls **through** the `overbought` threshold from above. Between crossings the strategy MUST persist the previously emitted signal (position-keeping behaviour).

#### Scenario: RSI crosses up through oversold threshold

- **WHEN** the prior-bar RSI ≤ `oversold` and the current-bar RSI > `oversold`
- **THEN** the strategy emits `+1` (enter long) for the current bar

#### Scenario: RSI crosses down through overbought threshold

- **WHEN** the prior-bar RSI ≥ `overbought` and the current-bar RSI < `overbought`
- **THEN** the strategy emits `0` (flat) for the current bar

#### Scenario: No crossing — position is held

- **WHEN** neither an oversold-up nor an overbought-down crossing occurs on the current bar
- **THEN** the strategy emits the same value as it emitted on the prior bar

#### Scenario: Initial period before any crossing

- **WHEN** no crossing event has occurred since the first valid RSI bar
- **THEN** the strategy emits `0` (flat) for all bars up to and including the first crossing

### Requirement: Lookahead-free RSI computation

The RSI value used to decide the signal at bar `t` MUST be computable strictly from closes at bars `t-1, t-2, ...` (i.e., MUST NOT consume `df["close"].iloc[t]`). The strategy MUST therefore apply `shift(1)` to the price series **before** computing rolling gain/loss.

#### Scenario: Signal on bar t excludes the current close

- **WHEN** the strategy computes its output for any bar `t`
- **THEN** the RSI series feeding the decision is derived from `df["close"].shift(1)` so that the close at bar `t` does not influence the bar-`t` signal

#### Scenario: Stacks with backtest's own shift safely

- **WHEN** `run_backtest` further applies `signal.shift(1) * daily_return` internally
- **THEN** the combined pipeline still produces a runnable result (no infinite-NaN propagation), and the strategy-layer shift does not introduce double-counting bias

### Requirement: Graceful behaviour under insufficient data

When the input DataFrame has fewer than `period + 1` rows, RSI is undefined for every bar. The strategy MUST NOT raise in that case.

#### Scenario: Cold start with too few bars

- **WHEN** `len(df) < period + 1`
- **THEN** the strategy returns a Series of zeros with `df.index` and integer dtype

#### Scenario: Just-enough data

- **WHEN** `len(df) >= period + 1` but RSI is NaN for the leading bars
- **THEN** the strategy emits `0` for every bar where RSI is undefined and only starts evaluating crossings once both prior-bar and current-bar RSI are defined

### Requirement: Long-only output

The strategy is intentionally long-only to keep the lesson narrative on entry/exit timing rather than short-side P&L. Values `-1` MUST NOT appear in the output.

#### Scenario: Output range is `{0, +1}`

- **WHEN** the strategy returns its Series
- **THEN** every value is either `0` or `+1`; no value equals `-1`

### Requirement: Documentation conventions

The implementation MUST follow project-wide doc conventions: Chinese docstrings and comments; English identifiers; UTC time handling inherited from the input `df` (no naive `datetime.now()` usage).

#### Scenario: Code review check

- **WHEN** a reviewer reads `project/strategies/rsi_reversal.py`
- **THEN** the module docstring and inline comments are in Chinese, function/variable names are English, and no naive datetime constructors are introduced
