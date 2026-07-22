from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

class IssueSeverity(Enum):
    WARNING = "warning"; ERROR = "error"

class CheckCategory(Enum):
    WATER_WATER = "water_water"; WATER_CAVITY = "water_cavity"; WATER_CORE = "water_core"
    WATER_EJECTOR = "water_ejector"; WATER_INSERT = "water_insert"; WATER_FASTENER = "water_fastener"

@dataclass
class Issue:
    category: CheckCategory; severity: IssueSeverity
    water_body_name: str; target_body_name: str
    distance: float; threshold: float; message: str
    point_a: Any = None; point_b: Any = None

    @property
    def is_violation(self): return self.distance < self.threshold

@dataclass
class CheckResult:
    issues: List[Issue] = field(default_factory=list)

    def add(self, issue): self.issues.append(issue)
    @property
    def total(self): return len(self.issues)

    @property
    def by_category(self):
        counts = {}
        for i in self.issues: counts[i.category] = counts.get(i.category, 0) + 1
        return counts

    @property
    def error_count(self): return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
    @property
    def warning_count(self): return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
