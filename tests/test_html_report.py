from src.report.models import CheckCategory, CheckResult, Issue, IssueSeverity
from src.report.html_report import render_html

def test_html(tmp_path):
    r=CheckResult()
    r.add(Issue(CheckCategory.WATER_WATER,IssueSeverity.ERROR,"A","B",1.5,3,"x"))
    o=tmp_path/"r.html"; render_html(r,o)
    c=o.read_text(encoding="utf-8")
    assert "A" in c and "B" in c and "water_water" in c
