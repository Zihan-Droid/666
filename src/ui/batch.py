from __future__ import annotations
import argparse
from src.geometry.classifier import Config
from src.nx_session import get_min_distance_info, get_session, redisplay_all
from src.report.highlight import highlight
from src.report.html_report import render_html
from src.report.models import CheckResult
from src.ui.block_ui import run_all_checks

def run(cfg, prt, rpt):
    get_session().Parts.OpenBaseDisplay(prt)
    config = Config.from_yaml(cfg)
    final, bodies = run_all_checks(config, get_min_distance_info)
    highlight(final, config, bodies)
    render_html(final, rpt)
    redisplay_all()
    return final

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--prt", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args(argv)
    r = run(a.config, a.prt, a.report)
    print(f"Done: {r.total} issues (Error {r.error_count} / Warning {r.warning_count})")
    print(f"Report: {a.report}")

if __name__ == "__main__": main()
