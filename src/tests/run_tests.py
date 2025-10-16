from os.path import dirname, abspath, join, relpath, split

from os import walk, unlink, sep as PATH_DELIM
import sys
import doctest
import traceback
import re
import unittest
import importlib
from typing import Any, List

OMIT_SLOW_TESTS = "--fast" in sys.argv

to_run = []
for a in sys.argv:
    if a.startswith("+"):
        to_run.append(a[1:])

UNITTEST_REGEXP = re.compile(r"^.*/test_[\w_]+.py$")
if PATH_DELIM != "/":
    UNITTEST_REGEXP = re.compile(r"^.*\\test_[\w_]+.py$")

MY_DIR = dirname(abspath(__file__))
ROOT = dirname(MY_DIR)
sys.path.append(ROOT)
# sys.path.append(join(ROOT, '..'))
try:
    sys.path.remove(MY_DIR)
except Exception:
    pass


def load_module_by_path(p: str) -> Any:
    if p.endswith(".py"):
        p = p[:-3]
    try:
        n = relpath(p, ROOT).replace(PATH_DELIM, ".")
        print("Loading", n, file=sys.stderr)
        # print(p, n, sys.path)
        return importlib.import_module(str(n))
    except BaseException:
        global num_failed
        num_failed += 1
        print(traceback.format_exc(), file=sys.stderr)
        print("Failed to load", p, file=sys.stderr)


def filter_file(p: str) -> bool:
    if to_run:
        n = split(p)[1]
        for tr in to_run:
            if n.find(tr) >= 0:
                return True
        else:
            return False
    if not OMIT_SLOW_TESTS:
        return True
    with open(p, "r") as f:
        for i in range(SCAN_LINES_NUM):
            s = f.readline()
            if s.find(SLOWTEST_CURSE) >= 0:
                return False
    return True


DOCTEST_CURSE = "# REGISTER_DOCTEST"
UNITTEST_CURSE = "# REGISTER_UNITTEST"
SLOWTEST_CURSE = "# SLOW_TEST"
SCAN_LINES_NUM = 10

num_failed = 0

suite = unittest.TestSuite()

dtp = doctest.DocTestParser()

doctest_files = []

p: str

for root, dirs, files in walk(ROOT):
    for fn in files:
        root: str = root
        dirs: List[str] = dirs
        files: List[str] = files
        p = join(root, fn)
        if p.endswith(".pyc"):
            unlink(p)


for root, dirs, files in walk(ROOT):
    if root.lower().count(PATH_DELIM + "venv" + PATH_DELIM) > 0:
        continue
    for fn in files:
        p = join(root, fn)
        if filter_file(str(p)):
            if fn.endswith(".doctest"):
                doctest_files.append(relpath(str(p), MY_DIR))
            elif UNITTEST_REGEXP.match(p):
                m = load_module_by_path(p)
                try:
                    suite.addTest(
                        unittest.TestSuite(
                            unittest.defaultTestLoader.loadTestsFromModule(m)
                        )
                    )
                except BaseException:
                    print("CANNOT MAKE A TEST SUITE FROM", p, file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    num_failed += 1
                    continue
            elif fn.endswith(".py"):
                with open(p, "r") as f:
                    for i in range(SCAN_LINES_NUM):
                        s = f.readline()
                        if s.find(DOCTEST_CURSE) >= 0:
                            try:
                                suite.addTest(
                                    doctest.DocTestSuite(load_module_by_path(p))
                                )
                            except BaseException:
                                print(
                                    "CANNOT MAKE A DOCTEST SUITE FROM",
                                    p,
                                    file=sys.stderr,
                                )
                                print(traceback.format_exc(), file=sys.stderr)
                                num_failed += 1
                                continue
                            break

suite.addTest(doctest.DocFileSuite(*doctest_files, module_relative=True))
runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)
if num_failed:
    print(
        "ERROR:",
        num_failed,
        "doctest(s) load failed, see the messages above",
        file=sys.stderr,
    )
if num_failed or not res.wasSuccessful():
    sys.exit(2)
sys.exit(0)
