"""NX 模具水路干涉审查工具 - 主入口。

支持两种模式:
  --mode ui      Tkinter 交互界面
  --mode batch   命令行批量处理
  --mode direct  直接模式（ListingWindow 输出，无 UI 依赖）

在 NX 内 [Tools] -> [Journal] -> [Run] 选择本文件即可运行。
"""
from __future__ import annotations
import os, sys

# 修复 NX2306 Tcl 版本不匹配：指向项目自带的 Tcl 库
_PROJ = os.path.dirname(os.path.abspath(__file__))
_TCL = os.path.join(_PROJ, "tcl")
os.environ["TCL_LIBRARY"] = os.path.join(_TCL, "tcl8.6")
os.environ["TK_LIBRARY"] = os.path.join(_TCL, "tk8.6")

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description="NX 模具水路干涉审查工具")
    parser.add_argument("--mode", choices=["ui", "batch", "direct"], default="ui",
                        help="运行模式: ui(交互界面) / batch(批量处理) / direct(直接模式)")
    parser.add_argument("--config", default=os.path.join(_PROJ, "config.json"),
                        help="配置文件路径 (默认: config.json)")
    parser.add_argument("--prt", help="要检查的 .prt 文件 (batch 模式必填)")
    parser.add_argument("--report", help="报告输出路径 (batch 模式必填)")
    args, _ = parser.parse_known_args(argv)

    if args.mode == "ui":
        try:
            from src.ui.block_ui import main as ui_main
            ui_main()
        except Exception as e:
            import NXOpen
            lw = NXOpen.Session.GetSession().ListingWindow
            lw.Open()
            lw.WriteLine("Tkinter UI 启动失败，回退到直接模式")
            lw.WriteLine(f"错误: {e}")
            lw.WriteLine("")
            _run_direct(args.config)
    elif args.mode == "direct":
        _run_direct(args.config)
    else:
        if not args.prt or not args.report:
            parser.error("batch 模式需要 --prt 和 --report 参数")
        from src.ui.batch import main as batch_main
        batch_main(["--config", args.config, "--prt", args.prt, "--report", args.report])


def _run_direct(config_path):
    """直接模式：结果输出到 ListingWindow + 生成 HTML 报告。"""
    import NXOpen
    from src.geometry.classifier import Config, Classifier, ComponentKind
    from src.geometry.collector import collect_bodies
    from src.checkers.water_water import WaterWaterChecker
    from src.checkers.water_cavity import WaterCavityChecker
    from src.checkers.water_ejector import WaterEjectorChecker
    from src.checkers.water_fastener import WaterFastenerChecker
    from src.report.models import CheckResult
    from src.report.html_report import render_html
    from src.nx_session import ask_min_distance, redisplay_all
    from src.report.highlight import highlight

    session = NXOpen.Session.GetSession()
    lw = session.ListingWindow
    lw.Open()
    lw.WriteLine("=" * 60)
    lw.WriteLine("  NX 模具水路干涉审查")
    lw.WriteLine("=" * 60)

    config = Config.from_json(config_path)
    lw.WriteLine(f"配置文件: {config_path}")

    bodies = collect_bodies(Classifier(config))
    lw.WriteLine(f"已识别 {len(bodies)} 个元件")
    for k in ComponentKind:
        n = sum(1 for b in bodies if b["kind"] == k)
        if n > 0:
            lw.WriteLine(f"  {k.value}: {n}")

    lw.WriteLine("")
    lw.WriteLine("正在检查...")

    distance_fn = ask_min_distance
    checkers = [
        WaterWaterChecker(config, distance_fn=distance_fn),
        WaterCavityChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.CAVITY),
        WaterCavityChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.CORE),
        WaterEjectorChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.EJECTOR),
        WaterEjectorChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.INSERT),
        WaterFastenerChecker(config, distance_fn=distance_fn),
    ]

    final = CheckResult()
    for c in checkers:
        sub = c.check(bodies)
        for issue in sub.issues:
            final.add(issue)

    lw.WriteLine("=" * 60)
    lw.WriteLine(f"检查完成: 共 {final.total} 项干涉")
    lw.WriteLine(f"  错误: {final.error_count}    警告: {final.warning_count}")
    lw.WriteLine("")

    for cat, n in final.by_category.items():
        lw.WriteLine(f"  {cat.value}: {n} 项")

    if final.issues:
        lw.WriteLine("")
        lw.WriteLine("-" * 60)
        for i, issue in enumerate(final.issues, 1):
            sev = "ERROR" if issue.severity.value == "error" else "WARNING"
            lw.WriteLine(f"{i}. [{issue.category.value}] {sev}")
            lw.WriteLine(f"   水路: {issue.water_body_name}")
            lw.WriteLine(f"   目标: {issue.target_body_name}")
            lw.WriteLine(f"   距离: {issue.distance:.2f}mm  阈值: {issue.threshold:.2f}mm")
    else:
        lw.WriteLine("")
        lw.WriteLine("  未发现干涉!")

    highlight(final, config, bodies)
    report_path = os.path.join(os.path.dirname(__file__), "report.html")
    render_html(final, report_path)
    redisplay_all()

    lw.WriteLine("")
    lw.WriteLine(f"报告: {report_path}")
    lw.WriteLine("干涉水路已在 NX 中高亮显示并分组")
    lw.WriteLine("=" * 60)


if __name__ == "__main__":
    main()
