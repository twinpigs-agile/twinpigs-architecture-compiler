import unittest
from os.path import join, dirname, relpath

from pc.common_utils.oneliners import TestIO
from pc.errorlog.error import StackedErrorContext, Severity
from pc.puml_compiler import puml_compiler
from tests.projects import PROJECTS


TESTFILES_BASE_PATH = dirname(__file__)
TESTFILE_SRC = "source.puml"
TESTFILE_MSG = "errors.msg"
TESTFILE_RES = "compiled.json"
TESTFILE_GMSG = "graphml.msg"
TESTFILE_GRAPHML = "compiled.graphml"


def get_test_function(src, msg, json, gmsg, graphml_path):
    src = relpath(src)

    def test_f(self):
        with open(msg, "rt", encoding="utf8") as fmsg:
            messages = fmsg.read()
        with open(json, "rt", encoding="utf8") as fjson:
            data = fjson.read()
        with open(gmsg, "rt", encoding="utf8") as fgmsg:
            gmessages = fgmsg.read()
        with open(graphml_path, "rt", encoding="utf8") as fgraphml:
            graphml = fgraphml.read()
        estr = TestIO()
        ec = StackedErrorContext(ofile=estr)
        _, json_res = puml_compiler(src, ec, True)
        self.assertEqual(estr.getvalue().replace("\r", ""), messages)
        if ec.max_severity < Severity.ERROR:
            self.assertEqual(json_res.replace("\r", ""), data)
        estr = TestIO()
        ec = StackedErrorContext(ofile=estr)
        _, g_res = puml_compiler(src, ec, False)
        self.assertEqual(estr.getvalue().replace("\r", ""), gmessages)
        # with open(join(TESTFILES_BASE_PATH, "prj_01/test.graphml"), 'wt', encoding='utf8') as of:
        #    of.write(g_res)
        if ec.max_severity < Severity.ERROR:
            self.assertMultiLineEqual(
                g_res.replace("\r", ""), graphml.replace("\r", "")
            )

    return test_f


def install_ext_tests(cls):

    for p in PROJECTS:
        bpath = join(TESTFILES_BASE_PATH, p)
        src_path = join(bpath, TESTFILE_SRC)
        msg_path = join(bpath, TESTFILE_MSG)
        res_path = join(bpath, TESTFILE_RES)
        gmsg_path = join(bpath, TESTFILE_GMSG)
        graphml_path = join(bpath, TESTFILE_GRAPHML)
        setattr(
            cls,
            "test_" + p,
            get_test_function(src_path, msg_path, res_path, gmsg_path, graphml_path),
        )


class PumlCompilerTest(unittest.TestCase):
    maxDiff = 16384 * 128


install_ext_tests(PumlCompilerTest)
