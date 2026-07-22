# NX 模具水路干涉审查工具 - 迭代日志

## 项目概述
基于 NX2306 NXOpen Python API 开发的模具水路干涉检查工具，支持 Tkinter 交互界面和批处理模式。

---

## 迭代 1：项目骨架搭建
- 确立项目结构：`src/checkers`、`src/geometry`、`src/report`、`src/ui`
- 实现配置驱动架构：`config.json` 管理层识别规则、颜色、阈值
- 设计数据模型：`Issue`、`CheckResult`、`CheckCategory`、`IssueSeverity`
- 实现几何分类器：按层/名称/属性识别水路、型腔、型芯、顶针、紧固件
- 实现 BBox 包围盒计算与预过滤
- 实现水路回路收集（MoldCooling API）

## 迭代 2：距离计算 API 探索（NX2306 兼容性）
- **问题**：NX2306 API 与旧版差异大，多种距离计算方法均不可用
  - `Session.UFSession` → 不存在，改用 `NXOpen.UF.UFSession.GetUFSession()`
  - `uf.UFEval` / `uf.UFModl` → 不存在，改用 `uf.Eval` / `uf.Modl`
  - `uf.Modl.AskMinimumDistData()` → 不存在
  - `SimpleInterference` → FirstBody/SecondBody 只读，Tag=0，PreviewBuilder 报错
  - `MeasureManager.GetMinimumDistance()` → 失败
- **解决**：`session.Measurement.GetMinimumDistance(body_a, body_b)` **可用**
  - 返回 `(distance, point_on_a, point_on_b, ...)`，取 `result[0]` 为距离

## 迭代 3：Tkinter UI 集成（NX 内启动）
- **问题**：NX2306 自带 tcl86t.dll v8.6.12 但 init.tcl 要求 8.6.7，Tcl 版本不匹配
- **解决**：复制 POSTBUILD Tcl 库文件，patch 版本号至 8.6.12，修复 UTF-8 BOM 问题
- 实现中文 Tkinter 界面：配置加载、类别勾选、阈值输入、进度显示、结果展示
- 添加批处理模式 `--config` `--prt` `--report` 命令行参数

## 迭代 4：干涉位置标记
- 检查时一次性获取最近点坐标存入 Issue（避免 highlight 阶段重复计算）
- 实现 Body 颜色高亮：水路红色(186)、目标体橙色(211)
- 实现干涉点标记：`work.Points.CreatePoint()` 创建可见点
- 实现球体标记（UF_MODL 缓存方法名，快速路径）

## 迭代 5：性能优化
- BBox 预过滤：bbox 间距 > 阈值直接跳过，不调用 API（大幅减少 API 调用）
- 球体创建方法缓存：首次查找后缓存，后续直接调用
- `redisplay_all()` 移除全局 Regenerate（大模型极慢），各 body 单独 Redisplay

## 迭代 6：UI 优化
- 窗口悬浮于 NX 之上（`topmost`）
- 分期显示进度：检查 → 高亮 → 报告 → 完成
- 下次运行自动清除上次标记：恢复 body 颜色，旧标记移到隐藏层
- 结果文本替换而非累加

## 迭代 7：项目整理
- 清理 23 个诊断/临时脚本
- 删除 `__pycache__`、`.pytest_cache`
- 目录结构规范化

---

## 技术要点

| 项目 | 说明 |
|------|------|
| NX 版本 | NX2306 |
| Python 环境 | NX 内置 Python 3.10，零外部依赖 |
| 距离 API | `session.Measurement.GetMinimumDistance()` |
| UI 框架 | Tkinter（内置，无需 pip） |
| 点标记 | `work.Points.CreatePoint()` |
| 体染色 | `body.Color = index` |
| Tcl 修复 | POSTBUILD tcl/tk 库 + 版本 patch |

## 检查类型

| 类别 | 阈值(默认mm) | 严重度 |
|------|-------------|--------|
| 水路-水路 | 3.0 | 错误 |
| 水路-型腔 | 15.0 | 错误 |
| 水路-型芯 | 15.0 | 错误 |
| 水路-顶针 | 3.0 | 错误 |
| 水路-镶件 | 3.0 | 错误 |
| 水路-紧固件 | 1.0 | 警告 |
