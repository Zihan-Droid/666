from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterFastenerChecker(InterferenceChecker):
    """水路与紧固件/标准件（螺丝、堵头、O 圈等）的干涉检查。"""
    category = CheckCategory.WATER_FASTENER
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.FASTENER

    def __init__(self, config, distance_fn: Callable):
        super().__init__(config)
        self._distance_fn = distance_fn

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        info = self._distance_fn(ctx.water_body, ctx.target_body)
        distance = info[0]
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold,
                                  severity=IssueSeverity.WARNING, point_a=info[1], point_b=info[2])
        return None
