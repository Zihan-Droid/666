from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
from src.geometry.classifier import Config
from src.report.models import CheckCategory, CheckResult
from src.nx_session import set_body_color, create_point_marker, create_highlight_at

def highlight(result, config, bodies):
    name_to_body = {b["name"]: b["body"] for b in bodies}
    by_cat = defaultdict(set)
    for issue in result.issues:
        body = name_to_body.get(issue.water_body_name)
        if body is not None:
            by_cat[issue.category].add(body)
    summary = {}
    for cat, members in by_cat.items():
        color = config.highlight_color(cat.value)
        for body in members:
            set_body_color(body, color)
        try:
            from src.nx_session import create_group
            create_group(list(members), f"{config.group_prefix}{cat.value.upper()}")
        except Exception:
            pass
        summary[cat.value] = len(members)

    # 干涉位置红色标记
    for issue in result.issues:
        water_body = name_to_body.get(issue.water_body_name)
        target_body = name_to_body.get(issue.target_body_name)
        try:
            if water_body is not None:
                set_body_color(water_body, 186)
            if target_body is not None:
                set_body_color(target_body, 211)
            if issue.point_a is not None:
                create_highlight_at(issue.point_a, 186)
                create_point_marker(issue.point_a.X, issue.point_a.Y, issue.point_a.Z, 186)
            if issue.point_b is not None:
                create_highlight_at(issue.point_b, 211)
                create_point_marker(issue.point_b.X, issue.point_b.Y, issue.point_b.Z, 211)
        except Exception:
            pass

    return summary
