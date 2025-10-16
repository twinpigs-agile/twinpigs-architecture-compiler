import unittest

from pc.astree.ast import AstNode, SourceRef
from pc.astree.ast_dump import AstDumpVisitor
from pc.common_utils.oneliners import TestIO


SRC_LINK0 = None
SRC_LINK1 = SourceRef()
SRC_LINK2 = SourceRef("f2")
SRC_LINK3 = SourceRef("f3", "l3")
SRC_LINK4 = SourceRef("f4", "l4", "c4")

SAMPLE_AST = AstNode(
    "root",
    SRC_LINK0,
    (
        AstNode(
            "add_op",
            SRC_LINK1,
            c_left=AstNode("1", SRC_LINK2),
            c_right=AstNode(
                "call", SRC_LINK3, [AstNode("const", SRC_LINK4, attr1="val1")]
            ),
        ),
    ),
    c_a1=AstNode("some_node"),
)

SAMPLE_AST_DUMP = """\
ast_node type="root"
 named_child name="a1":
  ast_node type="some_node"
   src: f="<None>"
 child:
  ast_node type="add_op"
   named_child name="left":
    ast_node type="1"
     src: f="f2"
   named_child name="right":
    ast_node type="call"
     src: f="f3", l="l3"
     child:
      ast_node type="const"
       src: f="f4", l="l4", c="c4"
       attr name="attr1": val1
"""

SAMPLE_AST_TEST_VISITOR_DUMP = ""


class AstTest(unittest.TestCase):
    maxDiff = 2048

    def test_dump(self):
        ostr = TestIO()
        AstDumpVisitor(SAMPLE_AST, ostr)
        self.assertEqual(ostr.getvalue(), SAMPLE_AST_DUMP)

    def test_flc(self):
        self.assertEqual(
            AstNode("t", src_ref=SourceRef("f", "l", "c")).get_flc(),
            {"f": "f", "l": "l", "c": "c"},
        )
