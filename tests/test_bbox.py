from src.geometry.bbox import BBox, bbox_distance, intersects

def test_bbox_distance_disjoint():
    assert bbox_distance(BBox(0,0,0,10,10,10), BBox(20,0,0,30,10,10)) == 10.0

def test_bbox_distance_overlapping():
    assert bbox_distance(BBox(0,0,0,10,10,10), BBox(5,5,5,15,15,15)) == 0.0

def test_intersects():
    a= BBox(0,0,0,10,10,10); b=BBox(12,0,0,20,10,10)
    assert intersects(a,b,5.0) is True
    assert intersects(a,b,1.0) is False
