from __future__ import annotations

def get_session():
    import NXOpen
    return NXOpen.Session.GetSession()

def get_work_part():
    session = get_session()
    work = session.Parts.Work
    if work is None: raise RuntimeError("No open work part.")
    return work

def get_moldcooling_manager():
    import NXOpen.MoldCooling
    return NXOpen.MoldCooling.Manager.GetManager(get_session())

def get_water_circuits(part=None) -> list:
    part = part or get_work_part()
    try:
        manager = get_moldcooling_manager()
        collection = manager.Circuits()
        circuits = []
        collection.GetCircuits(part, circuits)
        return circuits
    except Exception:
        return []

def ask_body_bbox(body):
    """获取 body 包围盒，返回 (xmin,ymin,zmin,xmax,ymax,zmax)。
    失败时返回极大默认值（跳过 bbox 预过滤优化，不影响检查正确性）。"""
    try:
        min_pt = [0.0, 0.0, 0.0]
        max_pt = [0.0, 0.0, 0.0]
        body.AskBoundingBox(min_pt, max_pt)
        return (min_pt[0], min_pt[1], min_pt[2], max_pt[0], max_pt[1], max_pt[2])
    except Exception:
        return (-1e9, -1e9, -1e9, 1e9, 1e9, 1e9)

def ask_min_distance(body_a, body_b) -> float:
    """计算两个 body 之间的最小距离 (mm)。使用 session.Measurement。"""
    session = get_session()
    result = session.Measurement.GetMinimumDistance(body_a, body_b)
    return result[0]

def get_min_distance_info(body_a, body_b):
    """返回 (distance, point_on_a, point_on_b)。用于创建干涉位置标记。"""
    session = get_session()
    result = session.Measurement.GetMinimumDistance(body_a, body_b)
    return (result[0], result[1], result[2])

def create_point_marker(x, y, z, color_index=186):
    """在指定坐标创建点标记（红色用于干涉位置）。"""
    import NXOpen
    work = get_work_part()
    pt3d = NXOpen.Point3d(x, y, z)
    point = work.Points.CreatePoint(pt3d)
    point.Color = color_index
    point.RedisplayObject()
    _created_objects.append(point)
    return point

RESULT_INTERFERENCE_EXISTS = 2

def set_body_color(body, color_index: int):
    tag = body.Tag
    if tag not in _colored_bodies:
        try:
            _colored_bodies[tag] = body.Color
        except Exception:
            _colored_bodies[tag] = 0
    body.Color = color_index; body.RedisplayObject()

_sphere_method = None  # 缓存的球体创建方法
_created_objects = []  # 本次创建的标记对象，用于清理
_colored_bodies = {}   # {body_tag: original_color} 被染色的 body，用于恢复

def _get_sphere_method():
    """获取 UF_MODL 球体创建方法，缓存结果。"""
    global _sphere_method
    if _sphere_method is False:
        return None
    if _sphere_method is not None:
        return _sphere_method
    import NXOpen
    try:
        ufs = NXOpen.UF.UFSession.GetUFSession()
        for name in ['CreateSphere1', 'CreateSph1', 'CreateSphere', 'create_sphere']:
            method = getattr(ufs.Modl, name, None)
            if method is not None:
                _sphere_method = method
                return method
    except Exception:
        pass
    _sphere_method = False
    return None

def create_highlight_at(point_3d, color_index=186):
    """在干涉位置创建高亮球体。方法缓存，快速路径。"""
    method = _get_sphere_method()
    if method is None:
        return None
    import NXOpen
    try:
        center = [point_3d.X, point_3d.Y, point_3d.Z]
        tag = method(0, center, 3.0)
        obj = NXOpen.TaggedObjectManager.GetTaggedObject(tag)
        if hasattr(obj, 'Color'):
            obj.Color = color_index
            obj.RedisplayObject()
        _created_objects.append(obj)
        return obj
    except Exception:
        return None

def create_group(members: list, name: str):
    group = get_work_part().Groups.CreateGroup(members)
    group.SetName(name); return group

def redisplay_all():
    """跳过全局 Regenerate（大模型很慢），各 body 已单独 Redisplay。"""
    pass

def clear_highlights():
    """清除上次检查的所有视觉标记。"""
    global _created_objects, _colored_bodies
    import NXOpen
    # 隐藏旧标记对象
    for obj in _created_objects:
        try:
            obj.Layer = 250  # 移到隐藏层
        except Exception:
            pass
    _created_objects = []
    # 恢复 body 颜色
    for tag, orig_color in list(_colored_bodies.items()):
        try:
            body = NXOpen.TaggedObjectManager.GetTaggedObject(tag)
            body.Color = orig_color
            body.RedisplayObject()
        except Exception:
            pass
    _colored_bodies = {}
