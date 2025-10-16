"""
# REGISTER_DOCTEST
>>> class Node1(Visited):
...     visited_type = 'n1'
...     def __init__(self, s):
...         self.s = s
...         self.children = (Node2(s + '_1'), Node2(s + '_2'), Node3(s + '_3'), Node4(s + '_4'), Node5(s + '_4'))
>>> class Node2(Visited):
...     visited_type = 'n2'
...     def __init__(self, s):
...         self.s = s
>>> class Node3(Visited):
...     visited_type = 'n3'
...     def __init__(self, s):
...         self.s = s
>>> class Node4(Visited):
...     visited_type = 'n2', 'n4'
...     def __init__(self, s):
...         self.s = s
>>> class Node5(Visited):
...     visited_type = 'n2', 'n5'
...     def __init__(self, s):
...         self.s = s
>>> class MyVisitor(Visitor):
...     def visit_n1(self, n, p1, p2):
...         print("n1_{0}_{1}".format(p1,p2))
...         return 1 + sum(i.accept_visitor(self, p1, p2=p2) for i in n.children)  # type: ignore
...     @staticmethod
...     def visit_n2(_, p1, p2):  # type: ignore
...         print("n2_{0}_{1}".format(p1,p2))
...         return 1
...     @staticmethod
...     def visit_n4(_, p1, p2):  # type: ignore
...         print("n4_{0}_{1}".format(p1,p2))
...         return 1
...     @staticmethod
...     def visit(_, p1, p2):  # type: ignore
...         print("unknown_{0}_{1}".format(p1,p2))
...         return 1
>>> class MyExtraVisitor(Visitor):
...     def fun_n1(self, n, p1, p2):
...         print("n1_{0}_{1}".format(p1,p2))
...         return 1 + sum(i.accept_visitor(self, p1, p2=p2, visitor_action='fun') for i in n.children)  # type: ignore
...     @staticmethod
...     def fun_n2(_, p1, p2):
...         print("n2_{0}_{1}".format(p1,p2))
...         return 1
...     @staticmethod
...     def fun_n4(_, p1, p2):
...         print("n4_{0}_{1}".format(p1,p2))
...         return 1
...     @staticmethod
...     def fun(_, p1, p2):
...         print("unknown_{0}_{1}".format(p1,p2))
...         return 1
>>> Node1("N1").accept_visitor(MyVisitor(), '1', p2='2')
n1_1_2
n2_1_2
n2_1_2
unknown_1_2
n4_1_2
n2_1_2
6
>>> Node1("N1").accept_visitor(MyExtraVisitor(), '1', p2='2', visitor_action='fun')
n1_1_2
n2_1_2
n2_1_2
unknown_1_2
n4_1_2
n2_1_2
6
"""

from typing import Any, Tuple


class Visitor(object):
    # def visit(self, obj, *a, **kw):
    #    return
    ...


class Visited(object):
    visited_type: Tuple[str, ...] = ()

    def accept_visitor(self, visitor: Any, *a: Any, **kw: str) -> Any:
        action_name = "visit"
        kwp = kw
        if "visitor_action" in kw:
            action_name = kw["visitor_action"]
            kwp = {a: b for a, b in kw.items() if a != "visitor_action"}
        vt: str
        for vt in reversed(
            self.visited_type
            if isinstance(self.visited_type, (list, tuple))
            else (self.visited_type,)
        ):
            method = getattr(visitor, action_name + "_" + vt, None)
            if method:
                break
        else:
            method = getattr(visitor, action_name)
        return method(self, *a, **kwp)
