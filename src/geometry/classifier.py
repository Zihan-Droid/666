from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ClassifierRule:
    name_patterns: List[str] = field(default_factory=list)
    layers: List[int] = field(default_factory=list)
    attributes: List[Dict[str, str]] = field(default_factory=list)


def _match_patterns(name: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def _match_attributes(attrs: Dict[str, str], rules: List[Dict[str, str]]) -> bool:
    for r in rules:
        if attrs.get(r["key"]) == r["value"]:
            return True
    return False


def classify_body(
    name: str,
    layer: int,
    attributes: Dict[str, str],
    rule: ClassifierRule,
    label: str = "water",
) -> Optional[str]:
    if rule.name_patterns and _match_patterns(name, rule.name_patterns):
        return label
    if rule.layers and layer in rule.layers:
        return label
    if rule.attributes and _match_attributes(attributes, rule.attributes):
        return label
    return None


class ComponentKind(Enum):
    WATER_LINE = "water_line"
    CAVITY = "cavity"
    CORE = "core"
    EJECTOR = "ejector"
    INSERT = "insert"
    FASTENER = "fastener"


class Config:
    """JSON 配置文件访问器。"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @classmethod
    def from_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def from_yaml(cls, path):
        # 兼容旧版 yaml 调用，内部转 json
        return cls.from_json(path)

    def rule(self, kind: ComponentKind) -> ClassifierRule:
        section = self._data["identification"].get(kind.value, {})
        return ClassifierRule(
            name_patterns=section.get("name_patterns", []),
            layers=section.get("layers", []),
            attributes=section.get("attributes", []),
        )

    def threshold(self, key: str) -> float:
        return float(self._data["thresholds"][key])

    def highlight_color(self, category: str) -> int:
        return int(self._data["highlight"]["colors"][category])

    @property
    def group_prefix(self) -> str:
        return self._data["highlight"]["group_prefix"]


class Classifier:
    def __init__(self, config: Config):
        self._config = config
        self._rules: Dict[ComponentKind, ClassifierRule] = {
            kind: config.rule(kind) for kind in ComponentKind
        }

    def classify(self, name: str, layer: int, attributes: Dict[str, str]) -> Optional[ComponentKind]:
        for kind, rule in self._rules.items():
            if classify_body(name, layer, attributes, rule, label=kind.value):
                return kind
        return None
