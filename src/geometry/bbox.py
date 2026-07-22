from __future__ import annotations
from dataclasses import dataclass

@dataclass
class BBox:
    xmin: float; ymin: float; zmin: float
    xmax: float; ymax: float; zmax: float

    @classmethod
    def from_tuple(cls, t):
        return cls(t[0], t[1], t[2], t[3], t[4], t[5])

def bbox_distance(a, b):
    dx = max(a.xmin - b.xmax, b.xmin - a.xmax, 0.0)
    dy = max(a.ymin - b.ymax, b.ymin - a.ymax, 0.0)
    dz = max(a.zmin - b.zmax, b.zmin - a.zmax, 0.0)
    return (dx*dx + dy*dy + dz*dz) ** 0.5

def intersects(a, b, tol):
    return bbox_distance(a, b) <= tol
