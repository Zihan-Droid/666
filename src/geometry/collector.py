from __future__ import annotations
from typing import Dict, List
from src.geometry.classifier import Classifier, ComponentKind
from src.geometry.bbox import BBox

def collect_bodies(classifier):
    from src.nx_session import ask_body_bbox, get_water_circuits, get_work_part
    work = get_work_part()
    bodies, circuit_tags = [], _collect_circuit_tags(work)
    for body in list(work.Bodies):
        name = body.Name or ""
        kind = classifier.classify(name, body.Layer, _read_attributes(body))
        if kind is None and body.Tag in circuit_tags: kind = ComponentKind.WATER_LINE
        if kind is None: continue
        bodies.append({"name": name or f"Body_{body.Tag}", "kind": kind, "body": body, "bbox": BBox.from_tuple(ask_body_bbox(body))})
    return bodies

def _collect_circuit_tags(part):
    from src.nx_session import get_water_circuits
    tags = set()
    for c in get_water_circuits(part):
        try:
            for m in c.GetMembers(): tags.add(m.Tag)
        except: tags.add(c.Tag)
    return tags

def _read_attributes(body):
    attrs = {}
    try:
        for t in body.GetUserAttributeTitles():
            v = body.GetStringUserAttribute(t, -1)
            if v is not None: attrs[t] = v
    except: pass
    return attrs
