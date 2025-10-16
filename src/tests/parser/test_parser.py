import unittest
from os.path import join, dirname, basename, relpath
from glob import glob

from pc.astree.ast_dump import AstDumpVisitor
from pc.common_utils.oneliners import TestIO
from pc.errorlog.error import StackedErrorContext, Severity
from pc.parser.parser import Parser
from pc.postparse.ppvisitors import PostParse


TESTFILES_PATH = join(dirname(__file__), "testfiles")
TESTFILES_POSTFIX = ".puml"
TESTFILES_MSG_POSTFIX = ".msg"
TESTFILES_AST_POSTFIX = ".ast"


def test_files(mask="success_*"):
    p = join(TESTFILES_PATH, mask + TESTFILES_POSTFIX)
    for src in glob(p):
        base = src[0 : -len(TESTFILES_POSTFIX)]
        tn = basename(src).split(".")[0]
        yield tn, src, base + TESTFILES_MSG_POSTFIX, base + TESTFILES_AST_POSTFIX


def get_test_function(src, msg, ast, severity):
    src = relpath(src)

    def test_f(self):
        tree = None
        with open(src, "rt", encoding="utf8") as fsrc:
            with open(msg, "rt", encoding="utf8") as fmsg:
                with (
                    open(ast, "rt", encoding="utf8")
                    if severity < Severity.WARNING
                    else fmsg
                ) as fast:
                    text = fsrc.read()
                    messages = fmsg.read()
                    if fast != fmsg:
                        tree = fast.read()
        estr = TestIO()
        ec = StackedErrorContext(ofile=estr)
        p = Parser("<FILE>", ec)
        r = p.parse(text)
        if ec.max_severity < Severity.ERROR:
            PostParse(r, ec)
        self.assertEqual(estr.getvalue(), messages)
        self.assertEqual(ec.max_severity, severity)
        if tree is not None:
            ostr = TestIO()
            AstDumpVisitor(r, ostr)
            self.assertEqual(ostr.getvalue().replace("\r", ""), tree)

    return test_f


def install_ext_tests(cls):
    for testname, src, msg, ast in test_files("success_*"):
        setattr(
            cls, "test_" + testname, get_test_function(src, msg, ast, Severity.NOTE)
        )

    for testname, src, msg, ast in test_files("error_*"):
        setattr(
            cls, "test_" + testname, get_test_function(src, msg, ast, Severity.ERROR)
        )

    for testname, src, msg, ast in test_files("fatal_*"):
        setattr(
            cls, "test_" + testname, get_test_function(src, msg, ast, Severity.FATAL)
        )


class ParserTest(unittest.TestCase):
    maxDiff = 16384


install_ext_tests(ParserTest)
