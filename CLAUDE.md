# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is **course material** for a 10-lesson training program on AI-driven software development ("AI 驱动的软件开发提效实战课"). It is not a product codebase. Each lesson lives in its own `lessonN/` directory with a `README.md` (student-facing handout), a `讲稿.md` (instructor speaking script), and a `demo/` folder containing runnable demo code.

The full course outline lives in `plan_v2.md` — read it before adding new lessons or deciding where to place new material.

## Demo structure: parallel `claude-demo` / `cursor-demo` is intentional

Inside `lesson1/demo/` there are two sibling folders — `claude-demo/` and `cursor-demo/` — that contain near-duplicate Python scripts (`btc_kline.py`). This duplication is **the entire point of Lesson 1**: students run the same prompt through Claude Code and Cursor and compare the two outputs side-by-side.

When editing demo code:
- Treat `claude-demo/` and `cursor-demo/` as independent artifacts, not as candidates for de-duplication or refactoring into a shared module.
- A change to one does **not** automatically need to be mirrored to the other; the divergence between them is part of the lesson.
- When in doubt about whether a change is "fixing a bug" or "erasing a teaching point," ask the user.

## Project conventions (from `.cursor/rules/project-conventions.mdc`)

These apply to all code in the repo, including demos:

1. **All time handling must be UTC.** Never use naive `datetime.now()`, `datetime.fromtimestamp(x)`, etc. Use `datetime.now(timezone.utc)` and `datetime.fromtimestamp(x, tz=timezone.utc)`. For pandas: `pd.to_datetime(..., utc=True)`. Print/log with explicit `Z` or `+00:00` suffix.
2. **All code comments and docstrings are written in Chinese.** Identifiers (variables, functions, classes) stay English; string literals follow business needs; only comments/docs are Chinese.
3. **Student-facing docs must be step-by-step followable.** Applies to `lesson*/README.md`, `lesson*/homework/**/*.md`, `demo/**/prompts/*.md` — any document a student is expected to follow. Each must include: prerequisites, numbered atomic steps with copy-pasteable commands/prompts, expected output for each step, cleanup/rollback commands, and common-error troubleshooting. Do **not** mix "instructor demo log" tone with "student walkthrough" tone — write imperatively for the student. Acceptance bar: a colleague who hasn't seen the lesson should be able to run it through without asking. **Excluded**: `lesson*/讲稿.md` (instructor speaking script, different audience).

The `cursor-demo/btc_kline.py` is the canonical example of the UTC convention applied (note `tz=timezone.utc` everywhere and the `tz_convert("UTC").tz_localize(None)` dance before handing to mplfinance, which requires a tz-naive index).

## Running the demo script

The Python demo has no `requirements.txt` — install ad hoc:

```bash
pip install requests pandas matplotlib mplfinance
```

Run from either demo folder:

```bash
# default: 1d candles, 30 days
python btc_kline.py

# other granularities
python btc_kline.py -i 1h         # 1-hour candles, default 14-day lookback
python btc_kline.py -i 5m -d 1    # 5-minute candles, 1-day lookback
```

Output PNG is written next to the script as `btc_kline_<interval>.png`. The script auto-selects the matplotlib `Agg` backend on headless Linux, so it runs cleanly in WSL/CI without a display.

## Linting

`ruff` is used (a `.ruff_cache/` exists at repo root and inside `claude-demo/`). There is no committed `pyproject.toml` or `ruff.toml`, so `ruff` runs with defaults:

```bash
ruff check .
```

There are no automated tests in this repo.
