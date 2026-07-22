"""NX 模具水路干涉审查 - Tkinter 交互界面。

在 NX 内通过 main.py --mode ui 启动，或直接由 main.py 默认启动。
"""
from __future__ import annotations
import os, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.geometry.classifier import Config, Classifier, ComponentKind
from src.geometry.collector import collect_bodies
from src.checkers.checkers import WaterWaterChecker, WaterCavityChecker, WaterEjectorChecker, WaterFastenerChecker
from src.report.models import CheckResult
from src.report.html_report import render_html

# 检查类别定义: (key, 中文标签, 配置键, 默认阈值mm)
CATEGORIES = [
    ("water_water",   "水路-水路",     "water_water_min",   3.0),
    ("water_cavity",  "水路-型腔",     "water_cavity_min",  15.0),
    ("water_core",    "水路-型芯",     "water_core_min",    15.0),
    ("water_ejector", "水路-顶针",     "water_ejector_min", 3.0),
    ("water_insert",  "水路-镶件",     "water_insert_min",  3.0),
    ("water_fastener","水路-紧固件",   "water_fastener_min",1.0),
]

_DEFAULT_ENABLED = {k: True for k, _, _, _ in CATEGORIES}


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def build_checkers(config, distance_fn, enabled):
    """根据启用的类别构建检查器列表。"""
    checkers = []
    if enabled.get("water_water"):
        checkers.append(WaterWaterChecker(config, distance_fn=distance_fn))
    if enabled.get("water_cavity"):
        checkers.append(WaterCavityChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.CAVITY))
    if enabled.get("water_core"):
        checkers.append(WaterCavityChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.CORE))
    if enabled.get("water_ejector"):
        checkers.append(WaterEjectorChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.EJECTOR))
    if enabled.get("water_insert"):
        checkers.append(WaterEjectorChecker(config, distance_fn=distance_fn, target_kind=ComponentKind.INSERT))
    if enabled.get("water_fastener"):
        checkers.append(WaterFastenerChecker(config, distance_fn=distance_fn))
    return checkers


def run_all_checks(config, distance_fn, enabled=None):
    """执行所有启用的检查，返回 (CheckResult, bodies列表)。"""
    if enabled is None:
        enabled = _DEFAULT_ENABLED
    bodies = collect_bodies(Classifier(config))
    final = CheckResult()
    for checker in build_checkers(config, distance_fn, enabled):
        sub = checker.check(bodies)
        for issue in sub.issues:
            final.add(issue)
    return final, bodies


class WaterCheckApp:
    """水路干涉审查主窗口。"""

    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("NX 模具水路干涉审查")
        master.geometry("780x680")
        master.minsize(620, 560)
        master.attributes('-topmost', True)  # 悬浮于 NX 之上

        self._config: Config | None = None
        self._cfg_path = tk.StringVar(value=os.path.join(_project_root(), "config.json"))
        self._rpt_path = tk.StringVar(value=os.path.join(_project_root(), "report.html"))

        # 启用状态 + 阈值
        self._enabled = {k: tk.BooleanVar(value=True) for k, _, _, _ in CATEGORIES}
        self._threshold = {k: tk.DoubleVar(value=d) for k, _, _, d in CATEGORIES}

        self._build_ui()
        self._load_config()

    # ── 界面构建 ──────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        # 配置文件区
        cfg_frame = ttk.LabelFrame(self.master, text="配置文件")
        cfg_frame.pack(fill="x", **pad)

        ttk.Label(cfg_frame, text="配置:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(cfg_frame, textvariable=self._cfg_path, width=52).grid(row=0, column=1, sticky="we", **pad)
        ttk.Button(cfg_frame, text="浏览...", command=self._browse_config).grid(row=0, column=2, **pad)
        ttk.Button(cfg_frame, text="加载", command=self._load_config).grid(row=0, column=3, **pad)

        ttk.Label(cfg_frame, text="报告:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(cfg_frame, textvariable=self._rpt_path, width=52).grid(row=1, column=1, sticky="we", **pad)
        ttk.Button(cfg_frame, text="浏览...", command=self._browse_report).grid(row=1, column=2, **pad)
        cfg_frame.columnconfigure(1, weight=1)

        # 检查类别 & 阈值区
        chk_frame = ttk.LabelFrame(self.master, text="检查类别与阈值")
        chk_frame.pack(fill="x", **pad)

        ttk.Label(chk_frame, text="启用").grid(row=0, column=0, **pad)
        ttk.Label(chk_frame, text="类别").grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(chk_frame, text="阈值 (mm)").grid(row=0, column=2, **pad)

        for i, (key, label, _, _) in enumerate(CATEGORIES, 1):
            ttk.Checkbutton(chk_frame, variable=self._enabled[key]).grid(row=i, column=0, **pad)
            ttk.Label(chk_frame, text=label).grid(row=i, column=1, sticky="w", **pad)
            ttk.Entry(chk_frame, textvariable=self._threshold[key], width=12).grid(row=i, column=2, sticky="w", **pad)

        # 全选/全不选
        sel_frame = ttk.Frame(chk_frame)
        sel_frame.grid(row=len(CATEGORIES) + 1, column=0, columnspan=3, sticky="w", **pad)
        ttk.Button(sel_frame, text="全选", command=lambda: self._toggle_all(True)).pack(side="left", padx=2)
        ttk.Button(sel_frame, text="全不选", command=lambda: self._toggle_all(False)).pack(side="left", padx=2)

        # 操作按钮区
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(fill="x", **pad)

        self._run_btn = ttk.Button(btn_frame, text="开始检查", command=self._run_check)
        self._run_btn.pack(side="left", **pad)

        ttk.Button(btn_frame, text="打开报告", command=self._open_report).pack(side="left", **pad)
        ttk.Button(btn_frame, text="关于", command=self._show_about).pack(side="left", **pad)
        ttk.Button(btn_frame, text="关闭", command=self.master.quit).pack(side="right", **pad)

        # 结果展示区
        result_frame = ttk.LabelFrame(self.master, text="检查结果")
        result_frame.pack(fill="both", expand=True, **pad)

        self._text = tk.Text(result_frame, height=16, wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        self._text.pack(side="left", fill="both", expand=True, **pad)
        scrollbar.pack(side="right", fill="y")

        # 结果显示样式
        self._text.tag_config("header", font=("Consolas", 10, "bold"))
        self._text.tag_config("error_tag", foreground="#cc0000")
        self._text.tag_config("warn_tag", foreground="#cc8800")
        self._text.tag_config("ok_tag", foreground="#008800")

        # 状态栏
        self._status = ttk.Label(self.master, text="就绪", relief="sunken", anchor="w")
        self._status.pack(fill="x", side="bottom")

    # ── 事件处理 ──────────────────────────────────────────────

    def _browse_config(self):
        path = filedialog.askopenfilename(
            initialdir=_project_root(),
            filetypes=[("JSON", "*.json"), ("所有文件", "*.*")]
        )
        if path:
            self._cfg_path.set(path)
            self._load_config()

    def _browse_report(self):
        path = filedialog.asksaveasfilename(
            initialdir=_project_root(),
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        if path:
            self._rpt_path.set(path)

    def _load_config(self):
        try:
            self._config = Config.from_json(self._cfg_path.get())
            # 从配置文件读取阈值
            for _, _, config_key, _ in CATEGORIES:
                try:
                    val = self._config.threshold(config_key)
                    if val is not None:
                        self._threshold[config_key.replace("_min", "")].set(val)
                except Exception:
                    pass
            self._status.config(text=f"已加载: {os.path.basename(self._cfg_path.get())}")
        except Exception as e:
            messagebox.showerror("配置错误", f"加载配置文件失败:\n{e}")
            self._config = None

    def _toggle_all(self, state: bool):
        for var in self._enabled.values():
            var.set(state)

    def _run_check(self):
        if self._config is None:
            return messagebox.showwarning("提示", "请先加载配置文件")

        # 收集阈值
        thresholds = {}
        for key, _, config_key, _ in CATEGORIES:
            try:
                thresholds[config_key] = float(self._threshold[key].get())
            except ValueError:
                return messagebox.showerror("输入错误", f"「{key}」阈值不是有效数字")
        self._config._data["thresholds"] = thresholds

        # 检查 NX 环境
        try:
            import NXOpen
        except ImportError:
            return messagebox.showerror("环境错误", "请在 NX 内运行: [工具] -> [操作记录] -> [播放...] -> 选择 main.py")

        enabled = {k: v.get() for k, v in self._enabled.items()}
        if not any(enabled.values()):
            return messagebox.showwarning("提示", "请至少选择一个检查类别")

        # 开始检查
        self._run_btn.config(state="disabled")
        self._status.config(text="正在检查...")
        self._text.delete("1.0", "end")
        self._text.insert("end", "正在执行干涉检查...\n\n")
        self.master.update()

        try:
            from src.nx_session import get_min_distance_info, redisplay_all, clear_highlights
            from src.report.highlight import highlight

            clear_highlights()  # 清除上次标记

            final, bodies = run_all_checks(self._config, get_min_distance_info, enabled)

            self._status.config(text="正在高亮干涉位置...")
            self._text.insert("end", "正在高亮...\n")
            self.master.update()
            highlight(final, self._config, bodies)

            self._status.config(text="正在生成报告...")
            self._text.insert("end", "正在生成报告...\n")
            self.master.update()
            render_html(final, self._rpt_path.get())

            redisplay_all()

            # 显示结果
            self._text.delete("1.0", "end")
            self._text.insert("end", f"=== 检查完成 ===\n", "header")
            self._text.insert("end", f"干涉总数: {final.total} 项\n")
            self._text.insert("end", f"  错误: {final.error_count}    警告: {final.warning_count}\n\n")

            if not final.issues:
                self._text.insert("end", "  未发现干涉问题!\n", "ok_tag")
            else:
                self._text.insert("end", "--- 按类别统计 ---\n")
                for cat_name, count in final.by_category.items():
                    self._text.insert("end", f"  {cat_name.value}: {count} 项\n")
                self._text.insert("end", "\n--- 详细列表 ---\n\n")

                for i, issue in enumerate(final.issues, 1):
                    tag = "error_tag" if issue.severity.value == "error" else "warn_tag"
                    sev_label = "错误" if issue.severity.value == "error" else "警告"
                    self._text.insert("end",
                        f"{i}. [{issue.category.value}] {sev_label}\n", tag)
                    self._text.insert("end",
                        f"   水路: {issue.water_body_name}\n"
                        f"   目标: {issue.target_body_name}\n"
                        f"   距离: {issue.distance:.2f}mm  /  阈值: {issue.threshold:.2f}mm\n"
                        f"   说明: {issue.message}\n\n")

            self._status.config(text=f"完成: 共 {final.total} 项干涉")

        except Exception as e:
            import traceback
            self._text.delete("1.0", "end")
            self._text.insert("end", f"检查失败:\n{traceback.format_exc()}\n", "error_tag")
            messagebox.showerror("检查失败", str(e))
            self._status.config(text="检查失败")

        finally:
            self._run_btn.config(state="normal")

    def _open_report(self):
        rpt = self._rpt_path.get()
        if not os.path.exists(rpt):
            return messagebox.showwarning("提示", "报告尚未生成，请先执行检查")
        os.startfile(rpt)

    def _show_about(self):
        messagebox.showinfo("关于",
            "NX 模具水路干涉审查工具 v1.0\n\n"
            "功能:\n"
            "  - 水路-水路 干涉检查\n"
            "  - 水路-型腔/型芯 干涉检查\n"
            "  - 水路-顶针/镶件 干涉检查\n"
            "  - 水路-紧固件 干涉检查\n\n"
            "基于 NXOpen Python API + Tkinter\n"
            "所有文件生成于 D:\\AI\\gansheTab\\"
        )


def main():
    root = tk.Tk()
    WaterCheckApp(root)
    root.mainloop()
