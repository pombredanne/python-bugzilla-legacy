
from __future__ import print_function

import atexit
import difflib
import imp
import os
import shlex
import sys

if sys.version_info.major >= 3:
    from io import StringIO
else:
    from StringIO import StringIO


_cleanup = []


def _import(name, path):
    _cleanup.append(path + "c")
    return imp.load_source(name, path)


def _cleanup_cb():
    for f in _cleanup:
        if os.path.exists(f):
            os.unlink(f)


atexit.register(_cleanup_cb)
bugzillascript = _import("bugzillascript", "bin/bugzilla")



def diff(orig, new):
    """
    Return a unified diff string between the passed strings
    """
    return "".join(difflib.unified_diff(orig.splitlines(1),
                                        new.splitlines(1),
                                        fromfile="Orig",
                                        tofile="New"))


def difffile(expect, filename):
    expect += '\n'
    if not os.path.exists(filename) or os.getenv("__BUGZILLA_UNITTEST_REGEN"):
        open(filename, "w").write(expect)
    ret = diff(open(filename).read(), expect)
    if ret:
        raise AssertionError("Output was different:\n%s" % ret)


def clicomm(argv, bzinstance, returnmain=False, printcliout=False,
            stdin=None, expectfail=False):
    """
    Run bin/bugzilla.main() directly with passed argv
    """

    argv = shlex.split(argv)

    oldstdout = sys.stdout
    oldstderr = sys.stderr
    oldstdin = sys.stdin
    oldargv = sys.argv
    try:
        if not printcliout:
            out = StringIO()
            sys.stdout = out
            sys.stderr = out
            if stdin:
                sys.stdin = stdin
        sys.argv = argv

        ret = 0
        mainout = None
        try:
            print(" ".join(argv))
            print()

            mainout = bugzillascript.main(bzinstance)
        except SystemExit:
            sys_e = sys.exc_info()[1]
            ret = sys_e.code

        outt = ""
        if not printcliout:
            outt = out.getvalue()
            if outt.endswith("\n"):
                outt = outt[:-1]

        if ret != 0 and not expectfail:
            raise RuntimeError("Command failed with %d\ncmd=%s\nout=%s" %
                               (ret, argv, outt))
        elif ret == 0 and expectfail:
            raise RuntimeError("Command succeeded but we expected success\n"
                               "ret=%d\ncmd=%s\nout=%s" % (ret, argv, outt))

        if returnmain:
            return mainout
        return outt
    finally:
        sys.stdout = oldstdout
        sys.stderr = oldstderr
        sys.stdin = oldstdin
        sys.argv = oldargv
