from __future__ import annotations

from pathlib import Path

from src.report.models import CheckResult


def render_html(result: CheckResult, output) -> None:
    """生成 HTML 报告（零外部依赖，纯字符串拼接）。"""
    issues_html = ""
    for i in result.issues:
        tag = i.severity.value
        issues_html += (
            '<tr>'
            f'<td>{i.category.value}</td>'
            f'<td class="{tag}">{tag.upper()}</td>'
            f'<td>{i.water_body_name}</td>'
            f'<td>{i.target_body_name}</td>'
            f'<td>{i.distance:.2f}</td>'
            f'<td>{i.threshold:.2f}</td>'
            f'<td>{i.message}</td>'
            '</tr>\n'
        )

    by_cat = ""
    for cat, n in result.by_category.items():
        by_cat += f"<li>{cat.value}: {n}</li>\n"

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>水路干涉审查报告</title>
  <style>
    body {{ font-family: "Microsoft YaHei", sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    .error {{ color: #c00; font-weight: bold; }}
    .warning {{ color: #c80; }}
    .summary {{ margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>水路干涉审查报告</h1>
  <div class="summary">
    <p>总计 <b>{result.total}</b> 项（错误 {result.error_count} / 警告 {result.warning_count}）</p>
    <ul>
      {by_cat}
    </ul>
  </div>
  <table>
    <thead>
      <tr><th>类别</th><th>严重性</th><th>水路</th><th>目标</th><th>距离(mm)</th><th>阈值(mm)</th><th>说明</th></tr>
    </thead>
    <tbody>
      {issues_html}
    </tbody>
  </table>
</body>
</html>"""
    Path(output).write_text(html, encoding="utf-8")
