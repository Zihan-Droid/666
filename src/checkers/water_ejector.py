from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterEjectorChecker(InterferenceChecker):
    """水路与顶针/镶件的间距检查。

    target_kind 默认 EJECTOR；集成层可通过构造参数切换为 INSERT。
    """
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.EJECTOR

    def __init__(self, config, distance_fn: Callable, target_kind: ComponentKind = ComponentKind.EJECTOR):
        super().__init__(config)
        self._distance_fn = distance_fn
        self.target_kind = target_kind

    @property
    def threshold_key(self) -> str:
        if self.target_kind == ComponentKind.INSERT:
            return "water_insert_min"
        return "water_ejector_min"

    @property
    def category(self) -> CheckCategory:
        if self.target_kind == ComponentKind.INSERT:
            return CheckCategory.WATER_INSERT
        return CheckCategory.WATER_EJECTOR

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        info = self._distance_fn(ctx.water_body, ctx.target_body)
        distance = info[0]
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold,
                                  severity=IssueSeverity.ERROR, point_a=info[1], point_b=info[2])
        return None
