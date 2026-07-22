from src.geometry.classifier import ClassifierRule, classify_body, _match_patterns, Classifier, Config, ComponentKind

def test_classify_by_name():
    r = ClassifierRule(name_patterns=["WL_*"])
    assert classify_body("WL_01",10,{},r)=="water"
    assert classify_body("X",10,{},r) is None

def test_classify_by_layer():
    assert classify_body("x",20,{},ClassifierRule(layers=[20]))=="water"
    assert classify_body("x",5,{},ClassifierRule(layers=[20])) is None

def test_classify_by_attr():
    r = ClassifierRule(attributes=[{"key":"T","value":"W"}])
    assert classify_body("x",10,{"T":"W"},r)=="water"
    assert classify_body("x",10,{"T":"E"},r) is None

def test_pattern_glob():
    assert _match_patterns("WL_01",["WL_*"]) is True
    assert _match_patterns("WL_01",["COOL*"]) is False

def test_classifier_config():
    cfg = Config({"identification":{
        "water_line":{"name_patterns":["WL_*"],"layers":[],"attributes":[]},
        "cavity":{"name_patterns":["CAV*"],"layers":[],"attributes":[]},
        "ejector":{"name_patterns":["EJ*"],"layers":[],"attributes":[]},
    },"thresholds":{"w":3},"highlight":{"colors":{"x":1},"group_prefix":"G_"}})
    clf = Classifier(cfg)
    assert clf.classify("WL_01",5,{})==ComponentKind.WATER_LINE
    assert clf.classify("CAV_01",5,{})==ComponentKind.CAVITY
    assert clf.classify("UNK",5,{}) is None
