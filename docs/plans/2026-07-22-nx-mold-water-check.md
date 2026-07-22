# NX 模具水路干涉审查 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 NX Open Python 的模具水路干涉审查工具，能在 NX 内自动识别水路与其他模具元件（水路、型腔/型芯、顶针/镶件、紧固件/标准件）的干涉，并高亮显示干涉水路、按类别分组，同时支持交互式自检和批处理审查。

**Architecture:** 分层架构 —— `nx_session` 负责会话与显示控制；`geometry` 负责按命名/层/属性识别水路与各类模具元件并做包围盒预筛；`checkers` 为每类干涉实现一个检查器（基类统一接口）；`report` 负责在 NX 内高亮、分组并生成 HTML 报告；`ui` 提供 NX Block UI 对话框（交互模式）和命令行批处理入口。纯几何/分类逻辑与 NX API 调用解耦，前者可用 pytest 单元测试，后者标记为集成测试在 NX 内运行。

**Tech Stack:** Python 3.10+、NX Open Python API (NXOpen, NXOpen.UF)、PyYAML（配置）、Jinja2（HTML 报告模板）、pytest（单测）、pytest-mock（mock NX API）。

---

## 项目目录结构

```
D:\AI\ganshe Tab\
├── README.md                        # 项目说明与使用方法
├── requirements.txt                 # Python 依赖
├── config.yaml                      # 检查规则配置（间距阈值、识别规则）
├── main.py                          # 总入口（dispatch 到 UI 或 batch）
├── src/
│   ├── __init__.py
│   ├── nx_session.py                # NX 会话管理、获取工作零件、显示控制
│   ├── geometry/
│   │   ├── __init__.py
│   │   ├── collector.py             # 遍历装配树收集 Solid/Body 对象
│   │   ├── classifier.py            # 按命名/层/属性识别水路与各类模具元件
│   │   └── bbox.py                  # 包围盒计算、最小距离预筛
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── base.py                  # InterferenceChecker 基类与 Issue 数据类
│   │   ├── water_water.py           # 水路-水路 检查
│   │   ├── water_cavity.py          # 水路-型腔/型芯 检查
│   │   ├── water_ejector.py         # 水路-顶针/镶件 检查
│   │   └── water_fastener.py        # 水路-紧固件/标准件 检查
│   ├── report/
│   │   ├── __init__.py
│   │   ├── models.py                # CheckResult / Issue 数据模型（纯数据）
│   │   ├── highlight.py             # NX 内高亮（变色 + 分组到 Group 对象）
│   │   ├── html_report.py           # Jinja2 渲染 HTML 报告
│   │   └── templates/
│   │       └── report.html.j2       # HTML 报告模板
│   └── ui/
│       ├── __init__.py
│       ├── block_ui.py              # NX Block UI 交互对话框
│       └── batch.py                 # 命令行批处理入口
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixture、mock NX session
│   ├── fixtures/                    # 测试 mock 数据
│   │   └── sample_config.yaml
│   ├── test_classifier.py
│   ├── test_bbox.py
│   ├── test_checkers.py
│   ├── test_models.py
│   └── test_html_report.py
└── docs/
    └── plans/
        └── 2026-07-22-nx-mold-water-check.md  # 本文件
```

## 文件职责说明

| 文件 | 职责 |
|------|------|
| `config.yaml` | 所有可调参数：水路命名前缀、层号映射、各检查类别间距阈值、高亮颜色 |
| `main.py` | 入口，解析 `--mode=ui\|batch`、`--config`、`--prt`，调用对应模块 |
| `src/nx_session.py` | 封装 `NXOpen.Session`、`Parts.Work`、`DisplayManager`，提供 `get_session()` / `get_work_part()` / `redisplay()` |
| `src/geometry/collector.py` | 递归遍历装配树，按 `Body`/`Face`/`Curve` 收集候选几何 |
| `src/geometry/classifier.py` | 按 name/layer/attribute 把几何归类为 `water/ cavity/core/ejector/insert/fastener` |
| `src/geometry/bbox.py` | `bbox_distance(a, b)` 返回包围盒最小距离；`intersects(a, b, tol)` 预筛 |
| `src/checkers/base.py` | `InterferenceChecker` 抽象基类：`check(geo) -> List[Issue]`；`Issue` 数据类 |
| `src/checkers/water_*.py` | 每个检查器实现一类干涉的成对检查 + 精确距离计算 |
| `src/report/models.py` | `CheckResult`（聚合所有 Issue）、`IssueSeverity` 枚举 |
| `src/report/highlight.py` | 把 Issue 涉及的水路改色、归入 NX Group 节点 |
| `src/report/html_report.py` | 渲染 HTML 报告（即使主输出是高亮，也附带报告便于审核留档） |
| `src/ui/block_ui.py` | NX Block Styler 对话框：选检查类别、阈值微调、运行、查看结果 |
| `src/ui/batch.py` | 命令行模式：批量处理多个 `.prt`，输出报告 |

---

## 任务分解

### Task 1: 项目骨架与配置

**Files:**
- Create: `D:\AI\ganshe Tab\README.md`
- Create: `D:\AI\ganshe Tab\requirements.txt`
- Create: `D:\AI\ganshe Tab\config.yaml`
- Create: `D:\AI\ganshe Tab\src\__init__.py`
- Create: `D:\AI\ganshe Tab\tests\__init__.py`
- Create: `D:\AI\ganshe Tab\tests\conftest.py`

- [ ] **Step 1: 创建 `requirements.txt`**

```
# NX Open Python API 由 NX 安装目录提供，不在此安装
pyyaml>=6.0
jinja2>=3.1
pytest>=7.4
pytest-mock>=3.12
```

- [ ] **Step 2: 创建 `config.yaml`**

```yaml
# 水路识别规则
identification:
  water_line:
    name_patterns: ["WL_*", "水路*", "COOL*"]
    layers: []
    attributes:
      - key: "MW_TYPE"
        value: "WATER_LINE"
  cavity:
    name_patterns: ["CAV*", "型腔*"]
  core:
    name_patterns: ["COR*", "型芯*"]
  ejector:
    name_patterns: ["EJ*", "顶针*", "PIN_*"]
  insert:
    name_patterns: ["INS*", "镶件*"]
  fastener:
    name_patterns: ["SCR*", "螺丝*", "PLUG*", "O_RING*"]

# 检查规则（单位 mm）
thresholds:
  water_water_min: 3.0
  water_cavity_min: 15.0
  water_core_min: 15.0
  water_ejector_min: 3.0
  water_insert_min: 3.0
  water_fastener_min: 1.0

# 高亮显示
highlight:
  colors:
    water_water: 1     # 红
    water_cavity: 6    # 黄
    water_core: 6
    water_ejector: 2   # 绿
    water_insert: 2
    water_fastener: 5  # 青
  group_prefix: "INTERFERENCE_"
```

- [ ] **Step 3: 创建 `src/__init__.py` 与 `tests/__init__.py`（空文件）**

```python
# src/__init__.py
```

```python
# tests/__init__.py
```

- [ ] **Step 4: 创建 `tests/conftest.py` —— mock NX Session 的公共 fixture**

```python
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture
def mock_nxopen(monkeypatch):
    """注入一个假的 NXOpen 模块，让纯逻辑测试不依赖 NX 安装。"""
    if "NXOpen" in sys.modules:
        del sys.modules["NXOpen"]
    fake = types.ModuleType("NXOpen")
    fake.Session = type("Session", (), {})
    monkeypatch.setitem(sys.modules, "NXOpen", fake)
    return fake


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent
```

- [ ] **Step 5: 创建 `README.md`**

```markdown
# NX 模具水路干涉审查工具

基于 NX Open Python 的模具水路干涉自动审查工具，支持水路与水路、型腔/型芯、顶针/镶件、紧固件/标准件之间的干涉检查，在 NX 内高亮显示干涉水路并按类别分组。

## 使用方式

### 交互模式（在 NX 内运行）
1. 打开 NX，菜单 [Tools] → [Journal] → [Run] 选择 `main.py`
2. 在弹出的 Block UI 对话框中选择检查类别与阈值
3. 点击 [Run] 执行检查
4. 干涉水路会被变色并归入 `INTERFERENCE_*` 分组

### 批处理模式
```bash
python main.py --mode batch --config config.yaml --prt "D:\molds\A.prt" --report out.html
```

## 依赖
- NX 2007+（自带 NX Open Python）
- 见 `requirements.txt`

## 开发
```bash
pip install -r requirements.txt
pytest
```
```

- [ ] **Step 6: 提交**

```bash
git init
git add README.md requirements.txt config.yaml src/__init__.py tests/__init__.py tests/conftest.py docs/plans/2026-07-22-nx-mold-water-check.md
git commit -m "chore: 初始化项目骨架与配置"
```

---

### Task 2: 报告数据模型（纯数据，可单测）

**Files:**
- Create: `D:\AI\ganshe Tab\src\report\__init__.py`
- Create: `D:\AI\ganshe Tab\src\report\models.py`
- Test: `D:\AI\ganshe Tab\tests\test_models.py`

- [ ] **Step 1: 写失败测试 `tests/test_models.py`**

```python
from src.report.models import Issue, IssueSeverity, CheckResult, CheckCategory


def test_issue_creation():
    issue = Issue(
        category=CheckCategory.WATER_WATER,
        severity=IssueSeverity.ERROR,
        water_body_name="WL_01",
        target_body_name="WL_02",
        distance=1.5,
        threshold=3.0,
        message="水路间距 1.5mm < 阈值 3.0mm",
    )
    assert issue.is_violation is True
    assert issue.category == CheckCategory.WATER_WATER


def test_check_result_summary():
    result = CheckResult()
    result.add(Issue(
        category=CheckCategory.WATER_WATER,
        severity=IssueSeverity.ERROR,
        water_body_name="WL_01",
        target_body_name="WL_02",
        distance=1.5,
        threshold=3.0,
        message="x",
    ))
    result.add(Issue(
        category=CheckCategory.WATER_CAVITY,
        severity=IssueSeverity.WARNING,
        water_body_name="WL_01",
        target_body_name="CAV",
        distance=12.0,
        threshold=15.0,
        message="y",
    ))
    assert result.total == 2
    assert result.by_category[CheckCategory.WATER_WATER] == 1
    assert result.by_category[CheckCategory.WATER_CAVITY] == 1
    assert result.error_count == 1
    assert result.warning_count == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_models.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'src.report.models'`

- [ ] **Step 3: 实现 `src/report/models.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class IssueSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"


class CheckCategory(Enum):
    WATER_WATER = "water_water"
    WATER_CAVITY = "water_cavity"
    WATER_CORE = "water_core"
    WATER_EJECTOR = "water_ejector"
    WATER_INSERT = "water_insert"
    WATER_FASTENER = "water_fastener"


@dataclass
class Issue:
    category: CheckCategory
    severity: IssueSeverity
    water_body_name: str
    target_body_name: str
    distance: float
    threshold: float
    message: str

    @property
    def is_violation(self) -> bool:
        return self.distance < self.threshold


@dataclass
class CheckResult:
    issues: List[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    @property
    def total(self) -> int:
        return len(self.issues)

    @property
    def by_category(self) -> Dict[CheckCategory, int]:
        counts: Dict[CheckCategory, int] = {}
        for issue in self.issues:
            counts[issue.category] = counts.get(issue.category, 0) + 1
        return counts

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
```

- [ ] **Step 4: 创建 `src/report/__init__.py`（空）**

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_models.py -v`
Expected: 2 passed

- [ ] **Step 6: 提交**

```bash
git add src/report/__init__.py src/report/models.py tests/test_models.py
git commit -m "feat: 添加报告数据模型 Issue/CheckResult"
```

---

### Task 3: 配置加载器与分类规则

**Files:**
- Create: `D:\AI\ganshe Tab\src\geometry\__init__.py`
- Create: `D:\AI\ganshe Tab\src\geometry\classifier.py`
- Test: `D:\AI\ganshe Tab\tests\test_classifier.py`

- [ ] **Step 1: 写失败测试 `tests/test_classifier.py`**

```python
from src.geometry.classifier import ClassifierRule, classify_body


def test_classify_by_name_pattern():
    rule = ClassifierRule(name_patterns=["WL_*", "水路*"], layers=[], attributes=[])
    assert classify_body("WL_01", layer=10, attributes={}, rule=rule) == "water"
    assert classify_body("水路-进水", layer=10, attributes={}, rule=rule) == "water"
    assert classify_body("CAV_01", layer=10, attributes={}, rule=rule) is None


def test_classify_by_layer():
    rule = ClassifierRule(name_patterns=[], layers=[20, 21], attributes=[])
    assert classify_body("body1", layer=20, attributes={}, rule=rule) == "water"
    assert classify_body("body1", layer=5, attributes={}, rule=rule) is None


def test_classify_by_attribute():
    rule = ClassifierRule(
        name_patterns=[],
        layers=[],
        attributes=[{"key": "MW_TYPE", "value": "WATER_LINE"}],
    )
    assert classify_body("body1", layer=10, attributes={"MW_TYPE": "WATER_LINE"}, rule=rule) == "water"
    assert classify_body("body1", layer=10, attributes={"MW_TYPE": "EJECTOR"}, rule=rule) is None


def test_pattern_glob_match():
    from src.geometry.classifier import _match_patterns
    assert _match_patterns("WL_01", ["WL_*"]) is True
    assert _match_patterns("WL_01", ["COOL*"]) is False
    assert _match_patterns("水路-01", ["水路*"]) is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `src/geometry/classifier.py`**

```python
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ClassifierRule:
    """识别某一类元件的规则（任一条件命中即归为该类）。"""
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
    """返回 label 表示命中，None 表示不命中。"""
    if rule.name_patterns and _match_patterns(name, rule.name_patterns):
        return label
    if rule.layers and layer in rule.layers:
        return label
    if rule.attributes and _match_attributes(attributes, rule.attributes):
        return label
    return None
```

- [ ] **Step 4: 创建 `src/geometry/__init__.py`（空）**

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_classifier.py -v`
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add src/geometry/__init__.py src/geometry/classifier.py tests/test_classifier.py
git commit -m "feat: 添加按命名/层/属性识别元件的分类规则"
```

---

### Task 4: 配置加载与元件归类（解析 config.yaml）

**Files:**
- Modify: `D:\AI\ganshe Tab\src\geometry\classifier.py`（追加 `Config` 与 `Classifier` 类）
- Test: `D:\AI\ganshe Tab\tests\test_classifier.py`（追加测试）

- [ ] **Step 1: 追加失败测试**

在 `tests/test_classifier.py` 末尾追加：

```python
from src.geometry.classifier import Classifier, Config, ComponentKind


def test_classifier_from_config_dict():
    cfg = Config({
        "identification": {
            "water_line": {"name_patterns": ["WL_*"], "layers": [], "attributes": []},
            "cavity": {"name_patterns": ["CAV*"], "layers": [], "attributes": []},
            "ejector": {"name_patterns": ["EJ*"], "layers": [], "attributes": []},
        },
        "thresholds": {"water_water_min": 3.0, "water_cavity_min": 15.0},
        "highlight": {"colors": {"water_water": 1}, "group_prefix": "INTERFERENCE_"},
    })
    clf = Classifier(cfg)
    assert clf.classify("WL_01", layer=5, attributes={}) == ComponentKind.WATER_LINE
    assert clf.classify("CAV_01", layer=5, attributes={}) == ComponentKind.CAVITY
    assert clf.classify("EJ_01", layer=5, attributes={}) == ComponentKind.EJECTOR
    assert clf.classify("UNKNOWN", layer=5, attributes={}) is None
    assert cfg.threshold("water_water_min") == 3.0
    assert cfg.highlight_color("water_water") == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL（Config / Classifier / ComponentKind 不存在）

- [ ] **Step 3: 追加实现到 `src/geometry/classifier.py`**

```python
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ComponentKind(Enum):
    WATER_LINE = "water_line"
    CAVITY = "cavity"
    CORE = "core"
    EJECTOR = "ejector"
    INSERT = "insert"
    FASTENER = "fastener"


class Config:
    """config.yaml 的访问器。"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

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
    """把一个 Body 的 (name, layer, attributes) 映射到 ComponentKind。"""

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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_classifier.py -v`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/geometry/classifier.py tests/test_classifier.py
git commit -m "feat: 添加 Config 与 Classifier，支持从 yaml 加载并归类元件"
```

---

### Task 5: 包围盒距离与预筛（纯几何，可单测）

**Files:**
- Create: `D:\AI\ganshe Tab\src\geometry\bbox.py`
- Test: `D:\AI\ganshe Tab\tests\test_bbox.py`

- [ ] **Step 1: 写失败测试 `tests/test_bbox.py`**

```python
from src.geometry.bbox import BBox, bbox_distance, intersects


def test_bbox_distance_disjoint():
    a = BBox(0, 0, 0, 10, 10, 10)
    b = BBox(20, 0, 0, 30, 10, 10)
    assert bbox_distance(a, b) == 10.0


def test_bbox_distance_overlapping():
    a = BBox(0, 0, 0, 10, 10, 10)
    b = BBox(5, 5, 5, 15, 15, 15)
    assert bbox_distance(a, b) == 0.0


def test_intersects_with_tolerance():
    a = BBox(0, 0, 0, 10, 10, 10)
    b = BBox(12, 0, 0, 20, 10, 10)
    # 距离 2，阈值 5 -> 命中
    assert intersects(a, b, tol=5.0) is True
    # 距离 2，阈值 1 -> 不命中
    assert intersects(a, b, tol=1.0) is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_bbox.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `src/geometry/bbox.py`**

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BBox:
    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    @classmethod
    def from_tuple(cls, t) -> "BBox":
        # NXOpen UF.UFEval.AskBoundingBox 返回 [xmin,ymin,zmin,xmax,ymax,zmax]
        return cls(t[0], t[1], t[2], t[3], t[4], t[5])


def bbox_distance(a: BBox, b: BBox) -> float:
    """两个轴对齐包围盒之间的最小距离（重叠时为 0）。"""
    dx = max(a.xmin - b.xmax, b.xmin - a.xmax, 0.0)
    dy = max(a.ymin - b.ymax, b.ymin - a.ymax, 0.0)
    dz = max(a.zmin - b.zmax, b.zmin - a.zmax, 0.0)
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def intersects(a: BBox, b: BBox, tol: float) -> bool:
    """预筛：包围盒距离 <= tol 才需要精确检查。"""
    return bbox_distance(a, b) <= tol
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_bbox.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add src/geometry/bbox.py tests/test_bbox.py
git commit -m "feat: 添加包围盒距离计算与预筛"
```

---

### Task 6: 检查器基类与 Issue 工厂

**Files:**
- Create: `D:\AI\ganshe Tab\src\checkers\__init__.py`
- Create: `D:\AI\ganshe Tab\src\checkers\base.py`
- Test: `D:\AI\ganshe Tab\tests\test_checkers.py`

- [ ] **Step 1: 写失败测试 `tests/test_checkers.py`**

```python
from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind, Config
from src.report.models import CheckCategory, IssueSeverity


class _StubChecker(InterferenceChecker):
    category = CheckCategory.WATER_WATER
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.WATER_LINE

    def _check_pair(self, ctx: PairCheckContext):
        if ctx.water_name == "WL_01" and ctx.target_name == "WL_02":
            return ctx.make_issue(distance=1.5, threshold=ctx.threshold, severity=IssueSeverity.ERROR)
        return None


def _config():
    return Config({
        "identification": {},
        "thresholds": {"water_water_min": 3.0},
        "highlight": {"colors": {}, "group_prefix": "INTERFERENCE_"},
    })


def test_checker_collects_issues():
    bodies = [
        {"name": "WL_01", "kind": ComponentKind.WATER_LINE, "bbox": None},
        {"name": "WL_02", "kind": ComponentKind.WATER_LINE, "bbox": None},
        {"name": "WL_03", "kind": ComponentKind.WATER_LINE, "bbox": None},
    ]
    checker = _StubChecker(_config())
    result = checker.check(bodies)
    assert result.total == 2  # (WL_01,WL_02) 和 (WL_02,WL_01) 各一次
    assert all(i.water_body_name in ("WL_01", "WL_02") for i in result.issues)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_checkers.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `src/checkers/base.py`**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

from src.geometry.classifier import ComponentKind, Config
from src.report.models import CheckCategory, CheckResult, Issue, IssueSeverity


@dataclass
class PairCheckContext:
    """单个 (水路, 目标) 配对的上下文，传给子类。"""
    water_name: str
    water_body: Any
    water_bbox: Any
    target_name: str
    target_body: Any
    target_bbox: Any
    threshold: float

    def make_issue(
        self,
        distance: float,
        threshold: float,
        severity: IssueSeverity,
        message: Optional[str] = None,
    ) -> Issue:
        msg = message or f"{self.water_name} 与 {self.target_name} 距离 {distance:.2f}mm < 阈值 {threshold:.2f}mm"
        return Issue(
            category=None,  # 由基类填入
            severity=severity,
            water_body_name=self.water_name,
            target_body_name=self.target_name,
            distance=distance,
            threshold=threshold,
            message=msg,
        )


class InterferenceChecker(ABC):
    """每类干涉检查的基类。子类只需实现 _check_pair。"""

    category: CheckCategory  # 子类声明
    water_kind: ComponentKind = ComponentKind.WATER_LINE
    target_kind: ComponentKind  # 子类声明

    def __init__(self, config: Config):
        self._config = config

    @property
    def threshold_key(self) -> str:
        return f"{self.category.value}_min"

    def check(self, bodies: List[dict]) -> CheckResult:
        result = CheckResult()
        threshold = self._config.threshold(self.threshold_key)
        waters = [b for b in bodies if b["kind"] == self.water_kind]
        targets = [b for b in bodies if b["kind"] == self.target_kind]
        for w in waters:
            for t in targets:
                if self._skip_self(w, t):
                    continue
                ctx = PairCheckContext(
                    water_name=w["name"], water_body=w.get("body"), water_bbox=w.get("bbox"),
                    target_name=t["name"], target_body=t.get("body"), target_bbox=t.get("bbox"),
                    threshold=threshold,
                )
                issue = self._check_pair(ctx)
                if issue is not None:
                    issue.category = self.category
                    result.add(issue)
        return result

    def _skip_self(self, w: dict, t: dict) -> bool:
        """水路-水路检查时跳过自己；其它类别水路不会和目标同类，无需跳过。"""
        return self.water_kind == self.target_kind and w["name"] == t["name"]

    @abstractmethod
    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        ...
```

- [ ] **Step 4: 创建 `src/checkers/__init__.py`（空）**

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_checkers.py -v`
Expected: 1 passed

- [ ] **Step 6: 提交**

```bash
git add src/checkers/__init__.py src/checkers/base.py tests/test_checkers.py
git commit -m "feat: 添加干涉检查器基类与配对上下文"
```

---

### Task 7: 四个具体检查器（基于精确距离）

> 说明：真实距离计算依赖 NX API。此处把"精确距离计算"抽象为 `distance_fn`，单测时用 mock；集成运行时由 `nx_session` 注入 `NXOpen.UF.UFEval` 实现。

**Files:**
- Create: `D:\AI\ganshe Tab\src\checkers\water_water.py`
- Create: `D:\AI\ganshe Tab\src\checkers\water_cavity.py`
- Create: `D:\AI\ganshe Tab\src\checkers\water_ejector.py`
- Create: `D:\AI\ganshe Tab\src\checkers\water_fastener.py`
- Test: `D:\AI\ganshe Tab\tests\test_checkers.py`（追加）

- [ ] **Step 1: 追加失败测试到 `tests/test_checkers.py`**

```python
from src.checkers.water_water import WaterWaterChecker
from src.checkers.water_cavity import WaterCavityChecker
from src.checkers.water_ejector import WaterEjectorChecker
from src.checkers.water_fastener import WaterFastenerChecker


def _mock_distance(distance_map):
    """返回一个 (w_body, t_body) -> distance 的函数。"""
    def _fn(w_body, t_body):
        key = (id(w_body), id(t_body))
        return distance_map.get(key, 999.0)
    return _fn


def test_water_water_checker_with_mock_distance():
    cfg = Config({
        "identification": {},
        "thresholds": {"water_water_min": 3.0},
        "highlight": {"colors": {}, "group_prefix": "INTERFERENCE_"},
    })
    b1 = object()
    b2 = object()
    bodies = [
        {"name": "WL_01", "kind": ComponentKind.WATER_LINE, "body": b1, "bbox": None},
        {"name": "WL_02", "kind": ComponentKind.WATER_LINE, "body": b2, "bbox": None},
    ]
    dist_fn = _mock_distance({(id(b1), id(b2)): 1.5, (id(b2), id(b1)): 1.5})
    checker = WaterWaterChecker(cfg, distance_fn=dist_fn)
    result = checker.check(bodies)
    assert result.total == 2
    assert result.issues[0].distance == 1.5


def test_water_cavity_checker_with_mock_distance():
    cfg = Config({
        "identification": {},
        "thresholds": {"water_cavity_min": 15.0},
        "highlight": {"colors": {}, "group_prefix": "INTERFERENCE_"},
    })
    w, c = object(), object()
    bodies = [
        {"name": "WL_01", "kind": ComponentKind.WATER_LINE, "body": w, "bbox": None},
        {"name": "CAV_01", "kind": ComponentKind.CAVITY, "body": c, "bbox": None},
    ]
    dist_fn = _mock_distance({(id(w), id(c)): 10.0})
    checker = WaterCavityChecker(cfg, distance_fn=dist_fn)
    result = checker.check(bodies)
    assert result.total == 1
    assert result.issues[0].severity == IssueSeverity.ERROR
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_checkers.py -v`
Expected: FAIL（四个子模块不存在）

- [ ] **Step 3: 实现 `src/checkers/water_water.py`**

```python
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
        distance = self._distance_fn(ctx.water_body, ctx.target_body)
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold, severity=IssueSeverity.ERROR)
        return None
```

- [ ] **Step 4: 实现 `src/checkers/water_cavity.py`**

```python
from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterCavityChecker(InterferenceChecker):
    category = CheckCategory.WATER_CAVITY
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.CAVITY

    def __init__(self, config, distance_fn: Callable):
        super().__init__(config)
        self._distance_fn = distance_fn

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        distance = self._distance_fn(ctx.water_body, ctx.target_body)
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold, severity=IssueSeverity.ERROR)
        return None
```

- [ ] **Step 5: 实现 `src/checkers/water_ejector.py`**

```python
from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterEjectorChecker(InterferenceChecker):
    """同时检查顶针与镶件。"""
    category = CheckCategory.WATER_EJECTOR
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.EJECTOR  # 镶件在集成层通过单独实例化（target_kind=INSERT）实现

    def __init__(self, config, distance_fn: Callable, target_kind: ComponentKind = ComponentKind.EJECTOR):
        super().__init__(config)
        self._distance_fn = distance_fn
        self.target_kind = target_kind

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        distance = self._distance_fn(ctx.water_body, ctx.target_body)
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold, severity=IssueSeverity.ERROR)
        return None
```

- [ ] **Step 6: 实现 `src/checkers/water_fastener.py`**

```python
from __future__ import annotations

from typing import Callable, Optional

from src.checkers.base import InterferenceChecker, PairCheckContext
from src.geometry.classifier import ComponentKind
from src.report.models import CheckCategory, Issue, IssueSeverity


class WaterFastenerChecker(InterferenceChecker):
    category = CheckCategory.WATER_FASTENER
    water_kind = ComponentKind.WATER_LINE
    target_kind = ComponentKind.FASTENER

    def __init__(self, config, distance_fn: Callable):
        super().__init__(config)
        self._distance_fn = distance_fn

    def _check_pair(self, ctx: PairCheckContext) -> Optional[Issue]:
        distance = self._distance_fn(ctx.water_body, ctx.target_body)
        if distance < ctx.threshold:
            return ctx.make_issue(distance=distance, threshold=ctx.threshold, severity=IssueSeverity.WARNING)
        return None
```

- [ ] **Step 7: 运行测试验证通过**

Run: `pytest tests/test_checkers.py -v`
Expected: 3 passed

- [ ] **Step 8: 提交**

```bash
git add src/checkers/water_water.py src/checkers/water_cavity.py src/checkers/water_ejector.py src/checkers/water_fastener.py tests/test_checkers.py
git commit -m "feat: 实现四类水路干涉检查器（依赖注入 distance_fn）"
```

---

### Task 8: NX 会话封装（集成层，标记集成测试）

**Files:**
- Create: `D:\AI\ganshe Tab\src\nx_session.py`
- Create: `D:\AI\ganshe Tab\src\geometry\collector.py`

> 说明：NX API 调用无法在普通环境运行，不写单元测试，改为在 NX 内手工运行验证。

- [ ] **Step 1: 实现 `src/nx_session.py`**

```python
from __future__ import annotations

from typing import List, Optional, Tuple

import NXOpen
import NXOpen.UF


def get_session() -> NXOpen.Session:
    return NXOpen.Session.GetSession()


def get_work_part() -> NXOpen.Part:
    session = get_session()
    work = session.Parts.Work
    if work is None:
        raise RuntimeError("当前没有打开的工作零件。")
    return work


def ask_body_bbox(body: NXOpen.Body) -> Tuple[float, float, float, float, float, float]:
    """返回 (xmin,ymin,zmin,xmax,ymax,zmax)。"""
    uf = get_session().UFSession
    bbox = [0.0] * 6
    uf.UFEval.Initialize(body.Tag)
    try:
        uf.UFEval.AskBoundingBox(body.Tag, bbox)
    finally:
        uf.UFEval.Terminate(body.Tag)
    return tuple(bbox)


def ask_min_distance(body_a: NXOpen.Body, body_b: NXOpen.Body) -> float:
    """两个 body 之间的最小距离（mm）。"""
    uf = get_session().UFSession
    info = NXOpen.UF.UFModl.AskMinimumDistData()
    uf.UFModl.AskMinimumDist(body_a.Tag, body_b.Tag, 0, [0.0, 0, 0], 0, [0.0, 0, 0], info)
    return info.distance


def set_body_color(body: NXOpen.DisplayableObject, color_index: int) -> None:
    body.Color = color_index
    body.RedisplayObject()


def create_group(members: List[NXOpen.DisplayableObject], name: str) -> NXOpen.Group:
    work = get_work_part()
    group = work.Groups.CreateGroup(members)
    group.SetName(name)
    return group


def redisplay_all() -> None:
    get_session().Parts.Work.Views.RedisplayObject()
```

- [ ] **Step 2: 实现 `src/geometry/collector.py`**

```python
from __future__ import annotations

from typing import Dict, List

import NXOpen

from src.geometry.classifier import Classifier, ComponentKind
from src.geometry.bbox import BBox
from src.nx_session import ask_body_bbox


def collect_bodies(classifier: Classifier) -> List[dict]:
    """遍历工作零件中的所有 Body，按 Classifier 分类并计算包围盒。"""
    from src.nx_session import get_work_part
    work = get_work_part()
    bodies: List[dict] = []
    for body in work.Bodies.ToArray():
        name = body.Name or ""
        layer = body.Layer
        attrs = _read_attributes(body)
        kind = classifier.classify(name, layer, attrs)
        if kind is None:
            continue
        bbox = BBox.from_tuple(ask_body_bbox(body))
        bodies.append({"name": name, "kind": kind, "body": body, "bbox": bbox})
    return bodies


def _read_attributes(body: NXOpen.DisplayableObject) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for title in body.GetUserAttributeTitles():
        value = body.GetStringUserAttribute(title, -1)
        if value is not None:
            attrs[title] = value
    return attrs
```

- [ ] **Step 3: 手工集成验证（在 NX 内运行）**

在 NX Journal 中运行如下脚本，确认能列出所有 Body 并打印分类：

```python
import sys
sys.path.insert(0, r"D:\AI\ganshe Tab")
from src.geometry.classifier import Config, Classifier
from src.geometry.collector import collect_bodies

cfg = Config.from_yaml(r"D:\AI\ganshe Tab\config.yaml")
clf = Classifier(cfg)
for b in collect_bodies(clf):
    print(b["name"], b["kind"])
```

Expected: 控制台打印每个识别到的 Body 名与类别；不报错。

- [ ] **Step 4: 提交**

```bash
git add src/nx_session.py src/geometry/collector.py
git commit -m "feat: 添加 NX 会话封装与装配 Body 收集器"
```

---

### Task 9: 高亮与分组（集成层）

**Files:**
- Create: `D:\AI\ganshe Tab\src\report\highlight.py`

- [ ] **Step 1: 实现 `src/report/highlight.py`**

```python
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from src.geometry.classifier import Config
from src.report.models import CheckCategory, CheckResult
from src.nx_session import create_group, set_body_color


def highlight(result: CheckResult, config: Config, bodies: List[dict]) -> Dict[str, int]:
    """按类别对干涉水路改色，并归入 INTERFERENCE_<category> 分组。

    返回每类命中数量，供 UI/报告显示。
    """
    name_to_body = {b["name"]: b["body"] for b in bodies}
    by_cat: Dict[CheckCategory, set] = defaultdict(set)
    for issue in result.issues:
        body = name_to_body.get(issue.water_body_name)
        if body is not None:
            by_cat[issue.category].add(body)

    summary: Dict[str, int] = {}
    for cat, members in by_cat.items():
        color = config.highlight_color(cat.value)
        for body in members:
            set_body_color(body, color)
        group_name = f"{config.group_prefix}{cat.value.upper()}"
        create_group(list(members), group_name)
        summary[cat.value] = len(members)
    return summary
```

- [ ] **Step 2: 手工集成验证**

在 NX Journal 中运行：

```python
import sys
sys.path.insert(0, r"D:\AI\ganshe Tab")
from src.geometry.classifier import Config, Classifier
from src.geometry.collector import collect_bodies
from src.checkers.water_water import WaterWaterChecker
from src.nx_session import ask_min_distance
from src.report.highlight import highlight

cfg = Config.from_yaml(r"D:\AI\ganshe Tab\config.yaml")
bodies = collect_bodies(Classifier(cfg))
checker = WaterWaterChecker(cfg, distance_fn=ask_min_distance)
result = checker.check(bodies)
print(highlight(result, cfg, bodies))
```

Expected: 干涉的水路变红，资源条出现 `INTERFERENCE_WATER_WATER` 分组。

- [ ] **Step 3: 提交**

```bash
git add src/report/highlight.py
git commit -m "feat: 添加 NX 内高亮与分组"
```

---

### Task 10: HTML 报告渲染

**Files:**
- Create: `D:\AI\ganshe Tab\src\report\templates\report.html.j2`
- Create: `D:\AI\ganshe Tab\src\report\html_report.py`
- Test: `D:\AI\ganshe Tab\tests\test_html_report.py`

- [ ] **Step 1: 写失败测试 `tests/test_html_report.py`**

```python
from pathlib import Path

from src.report.models import CheckCategory, CheckResult, Issue, IssueSeverity
from src.report.html_report import render_html


def test_render_html_contains_issues(tmp_path):
    result = CheckResult()
    result.add(Issue(
        category=CheckCategory.WATER_WATER,
        severity=IssueSeverity.ERROR,
        water_body_name="WL_01",
        target_body_name="WL_02",
        distance=1.5,
        threshold=3.0,
        message="x",
    ))
    out = tmp_path / "report.html"
    render_html(result, out)
    content = out.read_text(encoding="utf-8")
    assert "WL_01" in content
    assert "WL_02" in content
    assert "water_water" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_html_report.py -v`
Expected: FAIL

- [ ] **Step 3: 创建模板 `src/report/templates/report.html.j2`**

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>水路干涉审查报告</title>
  <style>
    body { font-family: "Microsoft YaHei", sans-serif; margin: 24px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
    th { background: #f0f0f0; }
    .error { color: #c00; font-weight: bold; }
    .warning { color: #c80; }
    .summary { margin-bottom: 16px; }
  </style>
</head>
<body>
  <h1>水路干涉审查报告</h1>
  <div class="summary">
    <p>总计 <b>{{ result.total }}</b> 项（错误 {{ result.error_count }} / 警告 {{ result.warning_count }}）</p>
    <ul>
      {% for cat, n in result.by_category.items() %}
      <li>{{ cat.value }}：{{ n }}</li>
      {% endfor %}
    </ul>
  </div>
  <table>
    <thead>
      <tr><th>类别</th><th>严重性</th><th>水路</th><th>目标</th><th>距离(mm)</th><th>阈值(mm)</th><th>说明</th></tr>
    </thead>
    <tbody>
      {% for i in result.issues %}
      <tr>
        <td>{{ i.category.value }}</td>
        <td class="{{ i.severity.value }}">{{ i.severity.value }}</td>
        <td>{{ i.water_body_name }}</td>
        <td>{{ i.target_body_name }}</td>
        <td>{{ "%.2f"|format(i.distance) }}</td>
        <td>{{ "%.2f"|format(i.threshold) }}</td>
        <td>{{ i.message }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
```

- [ ] **Step 4: 实现 `src/report/html_report.py`**

```python
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.report.models import CheckResult

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def render_html(result: CheckResult, output: Path | str) -> None:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    html = template.render(result=result)
    Path(output).write_text(html, encoding="utf-8")
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_html_report.py -v`
Expected: 1 passed

- [ ] **Step 6: 提交**

```bash
git add src/report/templates/report.html.j2 src/report/html_report.py tests/test_html_report.py
git commit -m "feat: 添加 HTML 报告渲染"
```

---

### Task 11: 交互式 Block UI 对话框

**Files:**
- Create: `D:\AI\ganshe Tab\src\ui\__init__.py`
- Create: `D:\AI\ganshe Tab\src\ui\block_ui.py`

> NX Block Styler 需要一个 `.dlx` 资源文件，由 NX 内的 Block UI Designer 创建。本任务给出 Python 端代码骨架，`.dlx` 文件由用户在 NX 中设计后放置到同目录。

- [ ] **Step 1: 实现 `src/ui/block_ui.py`**

```python
from __future__ import annotations

import os
import sys

import NXOpen
import NXOpen.BlockStyler

from src.geometry.classifier import Config, Classifier
from src.geometry.collector import collect_bodies
from src.checkers.water_water import WaterWaterChecker
from src.checkers.water_cavity import WaterCavityChecker
from src.checkers.water_ejector import WaterEjectorChecker
from src.checkers.water_fastener import WaterFastenerChecker
from src.geometry.classifier import ComponentKind
from src.nx_session import ask_min_distance, redisplay_all
from src.report.highlight import highlight
from src.report.html_report import render_html


class WaterCheckDialog(NXOpen.BlockStyler.UIBlock):
    def __init__(self):
        the_session = NXOpen.Session.GetSession()
        self.theUI = NXOpen.UI.GetUI()
        dlx_path = os.path.join(os.path.dirname(__file__), "WaterCheckDialog.dlx")
        if not os.path.exists(dlx_path):
            raise FileNotFoundError(f"缺少 Block UI 资源文件: {dlx_path}")
        self.theDialog = self.theUI.CreateDialog(dlx_path)
        self.theDialog.AddApplyHandler(self.apply_cb)
        self.theDialog.AddOkHandler(self.ok_cb)
        self.theDialog.AddInitializeHandler(self.initialize_cb)
        self._config = Config.from_yaml(os.path.join(_project_root(), "config.yaml"))

    def Show(self):
        self.theDialog.Show()

    def initialize_cb(self):
        pass

    def apply_cb(self):
        self._run_checks()

    def ok_cb(self):
        self._run_checks()

    def _run_checks(self):
        bodies = collect_bodies(Classifier(self._config))
        dist_fn = ask_min_distance
        checkers = [
            WaterWaterChecker(self._config, dist_fn),
            WaterCavityChecker(self._config, dist_fn),
            WaterEjectorChecker(self._config, dist_fn, target_kind=ComponentKind.EJECTOR),
            WaterEjectorChecker(self._config, dist_fn, target_kind=ComponentKind.INSERT),
            WaterFastenerChecker(self._config, dist_fn),
        ]
        from src.report.models import CheckResult
        final = CheckResult()
        for c in checkers:
            sub = c.check(bodies)
            for i in sub.issues:
                final.add(i)
        highlight(final, self._config, bodies)
        report_path = os.path.join(_project_root(), "report.html")
        render_html(final, report_path)
        redisplay_all()
        self.theUI.NXMessageDlg("检查完成：{} 项干涉，报告已写入 {}".format(final.total, report_path))


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    WaterCheckDialog().Show()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建 `src/ui/__init__.py`（空）**

- [ ] **Step 3: 手工集成验证**

在 NX 中：
1. 用 Block UI Designer 创建对话框（含一个 Apply 按钮），保存为 `src/ui/WaterCheckDialog.dlx`
2. Journal → Run 选择 `src/ui/block_ui.py`
3. 点击 Apply

Expected: 干涉水路变色、分组生成、`report.html` 生成、弹出统计对话框。

- [ ] **Step 4: 提交**

```bash
git add src/ui/__init__.py src/ui/block_ui.py
git commit -m "feat: 添加 NX Block UI 交互对话框"
```

---

### Task 12: 批处理入口与主入口

**Files:**
- Create: `D:\AI\ganshe Tab\src\ui\batch.py`
- Create: `D:\AI\ganshe Tab\main.py`

- [ ] **Step 1: 实现 `src/ui/batch.py`**

```python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src.geometry.classifier import Config, Classifier, ComponentKind
from src.geometry.collector import collect_bodies
from src.checkers.water_water import WaterWaterChecker
from src.checkers.water_cavity import WaterCavityChecker
from src.checkers.water_ejector import WaterEjectorChecker
from src.checkers.water_fastener import WaterFastenerChecker
from src.nx_session import ask_min_distance, get_session, redisplay_all
from src.report.highlight import highlight
from src.report.html_report import render_html
from src.report.models import CheckResult


def run(config_path: str, prt_path: str, report_path: str) -> CheckResult:
    session = get_session()
    session.Parts.OpenBaseDisplay(prt_path)

    config = Config.from_yaml(config_path)
    bodies = collect_bodies(Classifier(config))
    dist_fn = ask_min_distance

    checkers = [
        WaterWaterChecker(config, dist_fn),
        WaterCavityChecker(config, dist_fn),
        WaterEjectorChecker(config, dist_fn, target_kind=ComponentKind.EJECTOR),
        WaterEjectorChecker(config, dist_fn, target_kind=ComponentKind.INSERT),
        WaterFastenerChecker(config, dist_fn),
    ]
    final = CheckResult()
    for c in checkers:
        for i in c.check(bodies).issues:
            final.add(i)

    highlight(final, config, bodies)
    render_html(final, report_path)
    redisplay_all()
    return final


def main(argv=None):
    parser = argparse.ArgumentParser(description="批量水路干涉审查")
    parser.add_argument("--config", required=True)
    parser.add_argument("--prt", required=True, help="模具装配 prt 文件路径")
    parser.add_argument("--report", required=True, help="输出 HTML 报告路径")
    args = parser.parse_args(argv)

    result = run(args.config, args.prt, args.report)
    print(f"检查完成：共 {result.total} 项干涉（错误 {result.error_count} / 警告 {result.warning_count}）")
    print(f"报告已写入：{args.report}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 实现 `main.py`**

```python
from __future__ import annotations

import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="NX 模具水路干涉审查工具")
    parser.add_argument("--mode", choices=["ui", "batch"], default="ui")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--prt")
    parser.add_argument("--report")
    args, _ = parser.parse_known_args(argv)

    if args.mode == "ui":
        # 延迟导入，避免无 NX 环境时报错
        from src.ui.block_ui import main as ui_main
        ui_main()
    else:
        if not args.prt or not args.report:
            parser.error("batch 模式需要 --prt 和 --report")
        from src.ui.batch import main as batch_main
        batch_main(["--config", args.config, "--prt", args.prt, "--report", args.report])


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 手工集成验证**

```bash
# 在 NX 安装的 Python 环境中
python main.py --mode batch --config config.yaml --prt "D:\molds\A.prt" --report out.html
```

Expected: 控制台打印统计；`out.html` 生成；模型中干涉水路变色。

- [ ] **Step 4: 提交**

```bash
git add src/ui/batch.py main.py
git commit -m "feat: 添加批处理入口与主入口"
```

---

### Task 13: 端到端集成验证

**Files:**
- 无新增，仅验证

- [ ] **Step 1: 运行全部单元测试**

Run: `pytest -v`
Expected: 所有纯逻辑测试通过（7~8 个）

- [ ] **Step 2: 在 NX 内用真实模具装配运行批处理**

准备一份真实模具 `.prt`（含水路、型腔、顶针等），运行：

```bash
python main.py --mode batch --config config.yaml --prt "<真实模具.prt>" --report e2e.html
```

Expected:
- 控制台输出统计
- NX 中干涉水路变色并归入 `INTERFERENCE_*` 分组
- `e2e.html` 包含详细干涉列表

- [ ] **Step 3: 在 NX 内运行 UI 模式**

Journal → Run `main.py` → 弹出对话框 → Apply

Expected: 同 Step 2 结果，并弹出统计对话框。

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "test: 端到端集成验证通过"
```

---

## 验收清单

- [ ] `pytest -v` 全部纯逻辑测试通过
- [ ] 在 NX 内打开真实模具，批处理模式能输出统计与报告
- [ ] 干涉水路在 NX 内按类别变色并归入 `INTERFERENCE_*` 分组
- [ ] UI 模式对话框能正常弹出并运行
- [ ] HTML 报告包含所有干涉项、类别、距离、阈值
- [ ] 水路-水路、水路-型腔/型芯、水路-顶针/镶件、水路-紧固件/标准件四类检查全部覆盖

## 注意事项

1. **NX Open Python 版本**：需使用 NX 自带的 Python 解释器（通常在 `<NX>\NXBIN\python\python.exe`），不要用系统 Python 运行涉及 NX API 的代码。
2. **Block UI `.dlx` 文件**：`src/ui/WaterCheckDialog.dlx` 需在 NX 内用 Block UI Designer 设计并导出，本计划无法自动生成。
3. **性能**：水路-水路为 O(n²)，大型模具可能较慢；`bbox.py` 的预筛已在基类 `check()` 之外由调用者决定是否启用（后续可优化为在基类中先做 bbox 预筛再调 `_check_pair`）。
4. **距离精度**：`UFModl.AskMinimumDist` 返回的是曲面最小距离，已满足模具水路审查需求；若需更严格可改用 `Interference` API。
