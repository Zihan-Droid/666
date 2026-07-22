from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterCavityChecker(InterferenceChecker):
    """水路与型腔/型芯的间距检查。

    target_kind 默认 CAVITY；集成层可通过构造参数切换为 CORE。
    """
    category = CheckCategory.WATER_CAVITY
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.CAVITY

    def __init__(self, config, distance_fn: Callable, target_kind: ComponentKind = ComponentKind.CAVITY):
        super().__init__(config)
        self._distance_fn = distance_fn
        self.target_kind = target_kind

    @property
    def threshold_key(self) -> str:
        if self.target_kind == ComponentKind.CORE:
            return "water_core_min"
        return "water_cavity_min"

    @property
    def category(self) -> CheckCategory:
        if self.target_kind == ComponentKind.CORE:
            return CheckCategory.WATER_CORE
        return CheckCategory.WATER_CAVITY

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        info = self._distance_fn(ctx.water_body, ctx.target_body)
        distance = info[0]
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold,
                                  severity=IssueSeverity.ERROR, point_a=info[1], point_b=info[2])
        return None
