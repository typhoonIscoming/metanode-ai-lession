"""ORM 模型聚合：import 在此触发 Base.metadata 收集所有 6 张表。

注意：alembic/env.py 通过 `import btc_arb.models` 获取 metadata；
其它代码 import 具体 ORM 类时也应从子模块直接拿，避免循环依赖。
"""

from btc_arb.models.job_run import JobRun
from btc_arb.models.market import Market
from btc_arb.models.prediction import Prediction
from btc_arb.models.price_tick import PriceTick
from btc_arb.models.setting import Setting
from btc_arb.models.signal_event import SignalEvent

__all__ = [
    "JobRun",
    "Market",
    "Prediction",
    "PriceTick",
    "Setting",
    "SignalEvent",
]
