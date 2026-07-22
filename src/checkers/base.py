from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional
from src.geometry.classifier import ComponentKind, Config
from src.geometry.bbox import bbox_distance
from src.report.models import CheckCategory, CheckResult, Issue, IssueSeverity

@dataclass
class PairCheckContext:
    water_name: str; water_body: Any; water_bbox: Any
    target_name: str; target_body: Any; target_bbox: Any
    threshold: float

    def make_issue(self, distance, threshold, severity, message=None, point_a=None, point_b=None):
        return Issue(category=None, severity=severity, water_body_name=self.water_name,
                     target_body_name=self.target_name, distance=distance, threshold=threshold,
                     message=message or f"{self.water_name} vs {self.target_name}: {distance:.2f} < {threshold:.2f}",
                     point_a=point_a, point_b=point_b)

class InterferenceChecker(ABC):
    category: CheckCategory
    water_kind: ComponentKind = ComponentKind.WATER_LINE
    target_kind: ComponentKind

    def __init__(self, config): self._config = config

    @property
    def threshold_key(self): return f"{self.category.value}_min"

    def check(self, bodies):
        result = CheckResult()
        threshold = self._config.threshold(self.threshold_key)
        waters = [b for b in bodies if b["kind"] == self.water_kind]
        targets = [b for b in bodies if b["kind"] == self.target_kind]
        same_kind = self.water_kind == self.target_kind
        for i, w in enumerate(waters):
            for j, t in enumerate(targets):
                if same_kind and j <= i: continue
                # bbox 预过滤：bbox 间距 > 阈值则跳过，不调用 API
                wb = w.get("bbox"); tb = t.get("bbox")
                if wb is not None and tb is not None:
                    if bbox_distance(wb, tb) > threshold:
                        continue
                ctx = PairCheckContext(water_name=w["name"], water_body=w.get("body"),
                    water_bbox=wb, target_name=t["name"], target_body=t.get("body"),
                    target_bbox=tb, threshold=threshold)
                issue = self._check_pair(ctx)
                if issue is not None: issue.category = self.category; result.add(issue)
        return result

    @abstractmethod
    def _check_pair(self, ctx): ...
