from typing import IO

from pc.common_utils.visitor import Visitor
from pc.common_utils.oneliners import iter_dict_lexorder
from pc.astree.ast import SourceRef, AstNode


def srcref_to_str(sr: SourceRef) -> str:
    if sr and sr.f:
        if sr.ln:
            if sr.col:
                return 'f="{0}", l="{1}", c="{2}"'.format(sr.f, sr.ln, sr.col)
            else:
                return 'f="{0}", l="{1}"'.format(sr.f, sr.ln)
        else:
            return 'f="{0}"'.format(sr.f)
    return ""


class AstDumpVisitor(Visitor):
    def __init__(self, r: AstNode, f: IO[str], tabs: int = 0):
        r.accept_visitor(self, f, tabs)

    def visit_ast_node(self, n: AstNode, f: IO[str], tabs: int) -> None:
        print(" " * tabs + 'ast_node type="{0}"'.format(n.node_type), file=f)
        ss = srcref_to_str(n.src_ref)
        if ss:
            print(" " * (tabs + 1) + "src: {0}".format(ss), file=f)
        for k, v in iter_dict_lexorder(n.attrs):
            print(" " * (tabs + 1) + 'attr name="{0}": {1}'.format(k, v), file=f)
        for k, v in iter_dict_lexorder(n.named_children):
            print(" " * (tabs + 1) + 'named_child name="{0}":'.format(k), file=f)
            v.accept_visitor(self, f, tabs + 2)
        for c in n.children:
            print(" " * (tabs + 1) + "child:", file=f)
            c.accept_visitor(self, f, tabs + 2)
