# REGISTER_DOCTEST

from typing import Any, Optional, List, Dict, DefaultDict
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape

from pc.settings.settings import TEMPLATE_DIR

from pc.errorlog.error import StackedErrorContext


JINJA_GRAPHML = "graphml.xml"


def _build_tree(
    nodes: List[Dict[str, Any]],
    parent: int = -1,
    p_map: Optional[DefaultDict[int, List[Any]]] = None,
    n_map: Optional[Dict[int, Dict[str, Any]]] = None,
    depth: int = 0,
) -> Optional[List[Dict[str, Any]]]:
    if p_map is None or n_map is None:
        p_map = defaultdict(list)
        n_map = {}
        for n in nodes:
            n["children"] = []
            n_map[n["num_id"]] = n
            p_map[n["num_parent_id"]].append(n)
    for n in p_map[parent]:
        n["depth"] = depth
        _build_tree(nodes, n["num_id"], p_map, n_map, depth + 1)
    if parent != -1:
        n_map[parent]["children"] = p_map[parent]
        return None
    return p_map[parent]


_R = ["80", "A0", "C0", "E0", "FF"]
_G = ["80", "A0", "C0", "E0", "FF"]
_B = ["80", "A0", "C0", "E0", "FF"]

_COLORS = [
    r + g + b
    for r in _R
    for g in _G
    for b in _B
    if (r != g or g != b) and (r > "C0" or g > "C0" or b > "C0")
]


def _get_colors_dist(c1: str, c2: str) -> int:
    return sum(
        (abs(int(c1[b : b + 2], 16) - int(c2[b : b + 2], 16)) for b in (0, 2, 4)), 0
    )


def _lighten(c: str) -> str:
    r, g, b = 0xFF - int(c[0:2], 16), 0xFF - int(c[2:4], 16), 0xFF - int(c[4:6], 16)
    r = r // 2
    g = g // 2
    b = b // 2
    return f"{0xff - r:02x}{0xff - g:02x}{0xff - b:02x}"


def _get_best_color(color_dict: Dict[int, str], key: int) -> str:
    """
    >>> cd = {}
    >>> for ic in range(len(_COLORS)):
    ...     cc = _get_best_color(cd, ic)
    ...     assert ic in cd
    ...     assert cc in cd.values()
    ...     assert len(cd) == ic + 1
    >>> len(cd) == len(_COLORS)
    True
    >>> col = _get_best_color(cd, len(_COLORS))
    >>> (col == _COLORS[0], len(cd) == len(_COLORS) + 1)
    (True, True)
    """
    if key not in color_dict:
        maxmin_i = None
        maxmin_d = -1
        for mx_idx, nc in enumerate(_COLORS):
            min_d = 0xFFFFFFFF
            for i, c in color_dict.items():
                d = _get_colors_dist(c, nc)
                if d < min_d:
                    min_d = d
            if maxmin_i is None or min_d > maxmin_d:
                maxmin_i, maxmin_d = mx_idx, min_d
        if maxmin_d == 0 or maxmin_i is None:
            color_dict[key] = _COLORS[key % len(_COLORS)]
        else:
            color_dict[key] = _COLORS[maxmin_i]
    return color_dict[key]


def graphml(val: Dict[str, Any], _: StackedErrorContext) -> str:
    val["tree"] = _build_tree(val["objects"])
    cdict: Dict[int, str] = {}
    val["colors"] = lambda n: _get_best_color(cdict, hash(n))
    val["lighten"] = _lighten
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR, encoding="utf-8", followlinks=False),
        autoescape=select_autoescape(
            enabled_extensions=("xml",),
            default_for_string=True,
        ),
    )
    template = env.get_template(JINJA_GRAPHML)
    return template.render(**val)
