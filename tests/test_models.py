from src.report.models import CheckCategory, CheckResult, Issue, IssueSeverity

def test_issue():
    i = Issue(category=CheckCategory.WATER_WATER, severity=IssueSeverity.ERROR,
              water_body_name="A",target_body_name="B",distance=1.5,threshold=3.0,message="x")
    assert i.is_violation is True
    assert i.category == CheckCategory.WATER_WATER

def test_result():
    r = CheckResult()
    r.add(Issue(CheckCategory.WATER_WATER,IssueSeverity.ERROR,"A","B",1.5,3.0,"x"))
    r.add(Issue(CheckCategory.WATER_CAVITY,IssueSeverity.WARNING,"A","C",12.0,15.0,"y"))
    assert r.total==2
    assert r.by_category[CheckCategory.WATER_WATER]==1
    assert r.by_category[CheckCategory.WATER_CAVITY]==1
    assert r.error_count==1
    assert r.warning_count==1
