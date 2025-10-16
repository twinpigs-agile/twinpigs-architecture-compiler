# -*- coding: utf-8 -*-
from collections import OrderedDict
from typing import List, Dict, cast, Callable, Any
from pc.common_utils.visitor import Visitor
from pc.errorlog.error import Severity, StackedErrorContext
from pc.astree.ast import AstNode
import pc.settings.settings

_ = cast(Callable[[str], str], getattr(pc.settings.settings, "_"))


class PostParse(Visitor):
    def __init__(self, root: AstNode, error_context: StackedErrorContext):
        self.ids: List[str] = []
        self.names: List[str] = []
        self.nodes: List[AstNode] = []
        self.id_dict: Dict[str, int] = {}
        self.name_dict: Dict[str, int] = {}
        self.qnames_stack: List[str] = []
        self.qids_stack: List[str] = []
        self.ec = error_context
        root.accept_visitor(self, visitor_action="_collect_names")
        root.accept_visitor(self, visitor_action="_collect_links")
        root.accept_visitor(self, visitor_action="_finalize_nodetypes")

    def _fix_original(self, n: AstNode) -> None:
        self.ec.fix(
            Severity.NOTE,
            _("The object mentioned above: file {f}, line {l}, col {c}"),
            **n.get_flc()
        )

    def _check_idname(self, n: AstNode) -> bool:
        res = True
        if getattr(n, "id") in self.id_dict:
            self.ec.fix(
                Severity.ERROR,
                _(
                    "An object's ID duplicates another object's ID. ID={v}, file {f}, line {l}, col {c}"
                ),
                v=repr(n.id),
                **n.get_flc()
            )
            self._fix_original(self.nodes[self.id_dict[n.id]])
            res = False
        if n.id in self.name_dict:
            self.ec.fix(
                Severity.ERROR,
                _(
                    "An object's ID duplicates another object's name. ID/name={v}, file {f}, line {l}, col {c}"
                ),
                v=repr(n.id),
                **n.get_flc()
            )
            self._fix_original(self.nodes[self.name_dict[n.id]])
            res = False
        if n.name != n.id:
            if n.name in self.id_dict:
                self.ec.fix(
                    Severity.ERROR,
                    _(
                        "An object's name duplicates another object's ID. Name/ID={v}, file {f}, line {l}, col {c}"
                    ),
                    v=repr(n.name),
                    **n.get_flc()
                )
                self._fix_original(self.nodes[self.id_dict[n.name]])
                res = False

            if n.name in self.name_dict:
                self.ec.fix(
                    Severity.ERROR,
                    _(
                        "An object's name duplicates another object's name. name={v}, file {f}, line {l}, col {c}"
                    ),
                    v=repr(n.name),
                    **n.get_flc()
                )
                self._fix_original(self.nodes[self.name_dict[n.name]])
                res = False
        return res

    def _add_obj(self, n: AstNode) -> bool:
        if not self._check_idname(n):
            return False
        n.setattr("num_id", len(self.ids))
        self.id_dict[n.id] = len(self.ids)
        self.name_dict[n.name] = len(self.names)
        self.ids.append(n.id)
        self.names.append(n.name)
        self.nodes.append(n)
        assert len(self.ids) == len(self.names)
        assert len(self.nodes) == len(self.ids)
        return True

    def _collect_names_map(self, n: AstNode) -> bool:
        n.setattr("qualified_name_prefix", self.qnames_stack[:])
        n.setattr("qualified_id_prefix", self.qids_stack[:])

        parent_id = self.qids_stack[-1] if self.qids_stack else False
        num_parent = self.id_dict[self.qids_stack[-1]] if self.qids_stack else -1
        n.setattr("num_parent", num_parent)
        n.setattr("parent_id", parent_id)

        return self._add_obj(n)

    def _collect_names_rectangle(self, n: AstNode) -> bool:
        n.setattr("qualified_name_prefix", self.qnames_stack[:])
        n.setattr("qualified_id_prefix", self.qids_stack[:])
        self.qnames_stack.append(n.name)
        self.qids_stack.append(n.id)
        res = self._add_obj(n) and self._collect_names(n)
        del self.qnames_stack[-1]
        del self.qids_stack[-1]
        parent_id = self.qids_stack[-1] if self.qids_stack else False
        num_parent = self.id_dict[self.qids_stack[-1]] if self.qids_stack else -1
        n.setattr("num_parent", num_parent)
        n.setattr("parent_id", parent_id)
        return res

    def _collect_names(self, n: AstNode) -> bool:
        res = True
        for c in n.children:
            res = c.accept_visitor(self, visitor_action="_collect_names") and res
        return res

    def _check_link(self, n: AstNode, ref: str, attr_name: str) -> bool:
        n.setattr(attr_name, -1)
        if ref in self.ids:
            n.setattr(attr_name, self.id_dict[ref])
            return True
        self.ec.fix(
            Severity.ERROR,
            _("An unresolved object reference: {v}, file {f}, line {l}, col {c}"),
            v=repr(ref),
            **n.get_flc()
        )
        return False

    def _collect_links_link(self, n: AstNode) -> bool:
        return self._check_link(n, n.id1, "num_id1") and self._check_link(
            n, n.id2, "num_id2"
        )

    def _collect_links(self, n: AstNode) -> bool:
        res = True
        for c in n.children:
            res = c.accept_visitor(self, visitor_action="_collect_links") and res
        return res

    def _finalize_nodetypes_puml(self, n: AstNode) -> bool:
        self.object_counter = 0
        n.change_type("root")
        return self._finalize_nodetypes(n)

    def _finalize_nodetypes_rectangle(self, n: AstNode) -> bool:
        self.object_counter += 1
        oc = self.object_counter
        res = self._finalize_nodetypes(n)
        if oc == self.object_counter:
            n.change_type("ext_program_system")
        else:
            n.change_type("group")
        return res

    def _finalize_nodetypes_map(self, n: AstNode) -> bool:
        self.object_counter += 1
        self.properties: OrderedDict[str, Any] = OrderedDict()
        res = self._finalize_nodetypes(n)
        n.setattr("properties", self.properties)
        del self.properties
        n.change_type("program_system")
        return res

    def _finalize_nodetypes_property(self, n: AstNode) -> bool:
        if n.id in self.properties:
            self.ec.fix(
                Severity.ERROR,
                _(
                    "A duplicate property found in a map object, id={v}, file {f}, line {l}, col {c}"
                ),
                v=repr(n.id),
                **n.get_flc()
            )
            return False
        self.properties[n.id] = n.value
        return True

    def _finalize_nodetypes(self, n: AstNode) -> bool:
        res = True
        for c in n.children:
            res = c.accept_visitor(self, visitor_action="_finalize_nodetypes") and res
        return res


class GenData:
    def __init__(self, root: AstNode, error_context: StackedErrorContext):
        self.root = root
        self.ec = error_context
        self.objects: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        root.accept_visitor(self, visitor_action="_visit")

    def get_data(self) -> Dict[str, List[Dict[str, Any]]]:
        return {"objects": self.objects, "links": self.links}

    def _visit(self, n: AstNode) -> None:
        for c in n.children:
            c.accept_visitor(self, visitor_action="_visit")

    def _visit_group(self, n: AstNode) -> None:
        self.objects.append(
            {
                "type": "group",
                "num_id": n.num_id,
                "id": n.id,
                "name": n.name,
                "qid": ":".join(n.qualified_id_prefix + [n.id]),
                "qname": "→".join(n.qualified_id_prefix + [n.name]),
                "num_parent_id": n.num_parent,
                "parent_id": n.parent_id,
                "description": n.name,
                "src_ref": "File {f}, line {l}, column {c}".format(**n.get_flc()),
            }
        )
        for c in n.children:
            c.accept_visitor(self, visitor_action="_visit")

    def _visit_program_system(self, n: AstNode) -> None:
        decoder = {
            "Info": "description",
            "Stack": "stack",
            "Team": "team",
            "Env": "env",
        }
        props = {
            pv: getattr(n, "properties", {}).get(pn, "") for pn, pv in decoder.items()
        }
        props.update(
            {
                "type": n.node_type,
                "num_id": n.num_id,
                "id": n.id,
                "name": n.name,
                "qid": ":".join(n.qualified_id_prefix + [n.id]),
                "qname": "→".join(n.qualified_id_prefix + [n.name]),
                "num_parent_id": n.num_parent,
                "parent_id": n.parent_id,
                "src_ref": "File {f}, line {l}, column {c}".format(**n.get_flc()),
            }
        )

        self.objects.append(props)

    def _visit_ext_program_system(self, n: AstNode) -> None:
        self._visit_program_system(n)

    def _visit_link(self, n: AstNode) -> None:
        self.links.append(
            {
                "num_id1": n.num_id1,
                "num_id2": n.num_id2,
                "id1": n.id1,
                "id2": n.id2,
                "info": n.info,
                "_1to2": getattr(n, "_1to2"),
                "_2to1": getattr(n, "_2to1"),
                "src_ref": "File {f}, line {l}, column {c}".format(**n.get_flc()),
            }
        )
