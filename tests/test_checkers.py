from src.checkers.base import InterferenceChecker
from src.geometry.classifier import ComponentKind, Config
from src.report.models import CheckCategory, IssueSeverity
from src.checkers.checkers import WaterWaterChecker, WaterCavityChecker, WaterEjectorChecker

def _cfg():
    return Config({"identification":{},"thresholds":{"water_water_min":3,"water_cavity_min":15,"water_core_min":15,"water_ejector_min":3,"water_insert_min":3,"water_fastener_min":1},"highlight":{"colors":{},"group_prefix":"G_"}})

def _md(m):
    def f(a,b): return m.get((id(a),id(b)),999)
    return f

class _Stub(InterferenceChecker):
    category=CheckCategory.WATER_WATER; water_kind=ComponentKind.WATER_LINE; target_kind=ComponentKind.WATER_LINE
    def _check_pair(self,ctx):
        if ctx.water_name=="A" and ctx.target_name=="B": return ctx.make_issue(1.5,ctx.threshold,IssueSeverity.ERROR)

def test_base():
    bodies=[{"name":"A","kind":ComponentKind.WATER_LINE,"bbox":None},{"name":"B","kind":ComponentKind.WATER_LINE,"bbox":None},{"name":"C","kind":ComponentKind.WATER_LINE,"bbox":None}]
    assert _Stub(_cfg()).check(bodies).total==1

def test_water_water():
    a,b=object(),object()
    bodies=[{"name":"A","kind":ComponentKind.WATER_LINE,"body":a,"bbox":None},{"name":"B","kind":ComponentKind.WATER_LINE,"body":b,"bbox":None}]
    r=WaterWaterChecker(_cfg(),_md({(id(a),id(b)):1.5})).check(bodies)
    assert r.total==1 and r.issues[0].distance==1.5

def test_cavity():
    w,c=object(),object()
    bodies=[{"name":"W","kind":ComponentKind.WATER_LINE,"body":w,"bbox":None},{"name":"C","kind":ComponentKind.CAVITY,"body":c,"bbox":None}]
    assert WaterCavityChecker(_cfg(),_md({(id(w),id(c)):10})).check(bodies).total==1

def test_ejector():
    w,e=object(),object()
    bodies=[{"name":"W","kind":ComponentKind.WATER_LINE,"body":w,"bbox":None},{"name":"E","kind":ComponentKind.EJECTOR,"body":e,"bbox":None}]
    r=WaterEjectorChecker(_cfg(),_md({(id(w),id(e)):2})).check(bodies)
    assert r.total==1 and r.issues[0].category==CheckCategory.WATER_EJECTOR
