from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterWaterChecker(InterferenceChecker):
    category = CheckCategory.WATER_WATER
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.WATER_LINE

    def __init__(self, config, distance_fn: Callable):
        super().__init__(config)
        self._distance_fn = distance_fn

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        info = self._distance_fn(ctx.water_body, ctx.target_body)
        distance = info[0]
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold,
                                  severity=IssueSeverity.ERROR, point_a=info[1], point_b=info[2])
        return None
