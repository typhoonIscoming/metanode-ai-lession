"""B-02 验收：敏感字段 mask 行为。"""

from __future__ import annotations

import pytest

from btc_arb.schemas.setting import mask_secret


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("short", "***hidden***"),
        ("sk-1234567890ABCD", "sk-123***hidden***ABCD"),
        ("tvly-abcdefghijklmnop", "tvly-a***hidden***mnop"),
    ],
)
def test_mask_secret(raw: str | None, expected: str | None) -> None:
    assert mask_secret(raw) == expected
