# Bot mutating routes: HTMX-aware response — Design

**Date:** 2026-05-17
**Status:** Approved
**Scope:** v1.2.2（小修，UI 行为修正）

---

## 1. Problem

`bot_detail.html` 的「启动 / 停止」按钮包在普通 `<form method="post">` 里。点击 → 浏览器 POST 到 `/bots/{id}/start`（或 `/stop`）→ 路由返回 `partials/bots_table.html`（裸 partial，没有 base.html 外壳）→ 浏览器把这片裸 HTML 当成完整页面渲染 → **页面又丑又错位**（没顶栏、没主题色、只有几张悬浮的 bot 卡）。

## 2. Solution

3 个 mutating routes（`bot_start` / `bot_stop` / `bot_delete`）按 caller 类型分支：

- **HTMX 调用**（list 卡片，`HX-Request: true` header）→ 返回 `partials/bots_table.html` 用于 swap（**当前行为，不变**）
- **普通 form 提交**（detail 页，无 `HX-Request` header）→ `RedirectResponse(url=f"/bots/{bot_id}", status_code=303)`，浏览器跳回详情页，自动看到新状态

`bot_delete` 的非-HTMX 重定向特殊：bot 已 soft-deleted，不应该跳回 detail（会 404 或显示 deleted），而是 `RedirectResponse("/bots", 303)` 回列表。

## 3. Files

- `app/routes/bots.py`：3 个 handler 末尾加 if-`hx-request` 分支
- `tests/test_routes_bots.py`：加 3 个测试（start / stop / delete 各一个 redirect 测；至少一个 HX header 测确认 partial 路径仍工作）

模板 / CSS / 其它路由不动。

## 4. 实现细节

抽一个小 helper 放在 `bots.py` 末尾：

```python
def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"
```

在每个 handler 的最后两行（`bots = session.exec(...)...all()` 和 `return templates.TemplateResponse(...)`）之前判断：

```python
    if not _is_htmx(request):
        return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)
    bots = session.exec(...).all()
    positions = {...}
    return templates.TemplateResponse(request, "partials/bots_table.html", {"bots": bots, "positions": positions})
```

`bot_delete` 的 redirect 目标改为 `/bots`。

## 5. 测试

新增 3 测加到 `tests/test_routes_bots.py` 末尾：

```python
def test_bot_start_form_redirects_to_detail():
    """普通 form 提交（无 HX-Request header）→ 303 跳回 detail。"""
    with TestClient(app) as client:
        client.post("/bots", data={...}, follow_redirects=True)
        r = client.post("/bots/1/start", follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/bots/1"


def test_bot_stop_form_redirects_to_detail():
    """启动后 → 普通 stop form → 303 跳回 detail。"""
    # ... 创建 bot + start it via HX so it goes running, then POST /stop without HX
    ...


def test_bot_delete_form_redirects_to_list():
    """普通 delete form → 303 跳回 /bots 列表（不是 detail，因 bot 已 deleted）。"""
    ...


def test_bot_start_with_hx_request_returns_partial():
    """HTMX 调用仍返回 partial HTML。"""
    with TestClient(app) as client:
        client.post("/bots", data={...}, follow_redirects=True)
        r = client.post("/bots/1/start", headers={"HX-Request": "true"})
        assert r.status_code == 200
        assert "<table>" in r.text or "metrics" in r.text  # partial 有 metrics grid
```

## 6. 不动 + 不影响

- 现有 `test_create_bot_then_list_shows_it` 和 `test_delete_bot_soft_deletes` 不依赖这个分支（用 `follow_redirects=True`）—— 仍 PASS
- HTMX 路径不变 —— bots list 的 5s 轮询 + Start/Stop/Delete 按钮 swap 行为完全保留
- 模板不动
- 覆盖率应略升（HX 分支多了新测）

## 7. 验收

- 浏览器开 `/bots/{id}` 点「启动」→ 跳回 `/bots/{id}`，状态变绿，没有丑页面闪现
- 浏览器开 `/bots` 点卡片上「启动」→ 表格 HTMX-swap，无页面跳转
- 测试 60 + 3 = 63 + 2 skipped 全绿
