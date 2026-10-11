"""/strategies 列表页。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.strategies import STRATEGY_REGISTRY
from app.strategies.registry import STRATEGY_DESCRIPTIONS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_list(request: Request) -> HTMLResponse:
    items = [
        {
            "name": name,
            "defaults": entry.defaults,
            "description": STRATEGY_DESCRIPTIONS.get(name, ""),
        }
        for name, entry in STRATEGY_REGISTRY.items()
    ]
    return templates.TemplateResponse(
        request,
        "strategies.html",
        {"strategies": items},
    )
