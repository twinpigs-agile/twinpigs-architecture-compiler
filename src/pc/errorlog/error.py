# REGISTER_DOCTEST
"""
>>> from pc.common_utils.oneliners import TestIO
>>> of = TestIO(); bc = StackedErrorContext(ofile=of)
>>> c = StackedErrorContext(ofile=of, base=bc, message='MSG', severity=Severity.NOTE)
>>> c.fix(Severity.NOTE, "NOTE in c")
>>> c.fix(Severity.FATAL, "ERR in c")
>>> msg = Severity.MESSAGES[Severity.NOTE] + ": NOTE in c\\n"
>>> msg += Severity.MESSAGES[Severity.NOTE] + ': MSG\\n'
>>> msg += Severity.MESSAGES[Severity.FATAL] + ": ERR in c\\n"
>>> msg += Severity.MESSAGES[Severity.NOTE] + ': MSG\\n'
>>> assert msg == of.getvalue()
>>> assert bc.max_severity == Severity.FATAL
"""
from __future__ import annotations
from copy import deepcopy
from sys import stderr
from typing import NamedTuple, cast, Callable, IO, Any, Optional

import pc.settings.settings

_ = cast(Callable[[str], str], getattr(pc.settings.settings, "_"))


class CompilerResults(NamedTuple):
    exitcode: int
    output: str


class Severity(object):
    FATAL = 3
    ERROR = 2
    WARNING = 1
    NOTE = 0
    MESSAGES = [_("Note"), _("Warning"), _("Error"), _("Fatal")]


class StackedErrorContext(object):
    FATAL = Severity.FATAL
    ERROR = Severity.ERROR
    WARNING = Severity.WARNING
    NOTE = Severity.NOTE

    def __init__(
        self,
        base: Optional[StackedErrorContext] = None,
        severity: int = NOTE,
        message: str = "",
        ofile: IO[str] = stderr,
        **kw: Any,
    ):
        self.max_severity = Severity.NOTE

        """if not message:
            if 'file' in kw:
                message = _("Used from file {file}")
                if 'line' in kw:
                   message = _("Used from file {file}, line {line}")
                   if 'col' in kw:
                       message = _("Used from file {file}, line {line}, col {col}")
        """
        self.base = base
        self.kw = deepcopy(kw)
        self.message = message
        self.ofile = ofile
        if base:
            self.ofile = base.ofile
        self.severity = severity

    def fix(self, severity: int, message: str, **kw: Any) -> None:
        if severity > self.max_severity:
            self.max_severity = severity
        self.write(Severity.MESSAGES[severity] + ": " + message.format(**kw))
        if self.base:
            if self.base.max_severity < self.max_severity:
                self.base.max_severity = self.max_severity
            self.base.fix(self.severity, self.message, **self.kw)

    def write(self, s: str) -> None:
        print(s, file=self.ofile)
