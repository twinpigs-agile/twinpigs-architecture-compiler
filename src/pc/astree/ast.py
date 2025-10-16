from __future__ import annotations
from typing import Any, Optional, Dict, Union, List, cast
from copy import copy, deepcopy
from os.path import sep

from pc.common_utils.visitor import Visited


class SourceRef(object):
    def __init__(
        self,
        f: Optional[str] = None,
        ln: Optional[int] = None,
        col: Optional[str] = None,
    ):
        if f:
            f = f.replace(sep, "/").replace("\\", "/")
        self.f, self.ln, self.col = f, ln, col


CHILD_PREFIX = "c_"
CHILD_PREFIX_LEN = len(CHILD_PREFIX)


class AstNode(Visited):
    def __init__(
        self,
        node_type: str,
        src_ref: SourceRef = SourceRef("<None>"),
        children: Optional[List[AstNode]] = None,
        **named_children_and_attrs: Any,
    ):
        """
        Attention: named_children_and_attrs keys and values are processed in a rather complicated way.

        If a key looks like 'c_XXX', it defines a child node named XXX (AstNode type assumed). Key 'XXX' is added
        to self.named_children, and XXX field is added to AstNode object fields.

        If a key does not start with 'c_', it goes to self.attrs (and to AstNode object fields as well).
        """
        attrs = {
            k: v
            for k, v in named_children_and_attrs.items()
            if not k.startswith(CHILD_PREFIX)
        }
        nc = {
            k[CHILD_PREFIX_LEN:]: v
            for k, v in named_children_and_attrs.items()
            if k.startswith(CHILD_PREFIX)
        }
        self.node_type = node_type
        self.visited_type = ("ast_node", node_type)
        self.src_ref = deepcopy(src_ref)
        if self.src_ref and self.src_ref.f:
            self.src_ref.f = self.src_ref.f.replace(sep, "/").replace("\\", "/")
        self.children: List[AstNode] = (
            copy(children) if children is not None else cast(List[AstNode], [])
        )
        self.attrs: Dict[str, Any] = {}  # copy(attrs)
        self.named_children = nc
        for k, v in nc.items():
            setattr(self, k, v)
        for k, v in attrs.items():
            self.attrs[k] = v

    def __getattr__(self, name: str) -> Any:
        if name in self.attrs:
            return self.attrs[name]
        if name in self.__dict__:
            return self.__dict__[name]
        raise AttributeError(f"{self.__class__} has no attribute {name}")

    def setattr(self, name: str, val: Any) -> None:
        self.attrs[name] = val

    def change_type(self, type_name: str) -> None:
        self.node_type = type_name
        self.visited_type = ("ast_node", type_name)

    def get_flc(self) -> Dict[str, Optional[Union[int, str]]]:
        return {"f": self.src_ref.f, "l": self.src_ref.ln, "c": self.src_ref.col}
