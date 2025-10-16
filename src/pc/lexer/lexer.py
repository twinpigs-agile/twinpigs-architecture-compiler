from __future__ import annotations

from typing import cast, Callable, Any, Optional
from ast import literal_eval

import pc.settings.settings
from pc.errorlog.error import StackedErrorContext
from pc.common_utils.source import Source
from pc.lexer.plylex_types import lex, LexToken, TOKEN


_ = cast(Callable[[str], str], getattr(pc.settings.settings, "_"))


class Lexer:
    """Build, then input(), then token gets tokens"""

    source_obj: Source

    def __init__(self, error_context: StackedErrorContext, filename: str) -> None:
        """Create a new Lexer."""
        self.filename = filename
        self.error_context = error_context

    def build(self, **kwargs: Any) -> None:
        """Builds the lexer from the specification. Must be
        called after the lexer object is created.

        This method exists separately, because the PLY
        manual warns against calling lex.lex inside
        __init__
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def input(self, text: str) -> None:
        self.result = True
        self.lexer.begin("INITIAL")
        self.lexer.input(text + "\n")

    def token(self) -> Optional[LexToken]:
        g = self.lexer.token()
        if not g:
            if self.lexer.current_state() == "ccomment":
                self.error_context.fix(
                    self.error_context.FATAL,
                    _("A C-style comment should be closed before EOF in {file}"),
                    file=self.filename,
                )
        return g

    def _error(self, msg: str, token: LexToken, **kw: Any) -> None:
        location = self.source_obj.get_lc(token.lexpos)
        self.error_context.fix(
            self.error_context.FATAL,
            msg,
            line=location[0],
            col=location[1],
            file=self.filename,
            **kw,
        )
        # self.lexer.skip(1) # A damned skip! I've nearly become crazy getting that a symbol is lost after an error!

    states = (
        ("strstate", "exclusive"),
        ("cppcomment", "exclusive"),
        ("ccomment", "exclusive"),
        ("propstate", "exclusive"),
        ("lnkinfostate", "exclusive"),
    )

    keywords = (
        "RECTANGLE",
        "AS",
        "MAP",
        "SERVICE",
        "GROUP",
        "COMPUTER",
        "CONTAINER",
        "CONTAINERS",
        "VM",
        "EXTERNAL",
    )

    keyword_map = {k.lower(): k for k in keywords}

    tokens = keywords + (
        "ID",
        "STRING_LITERAL",
        "PROPERTY_VALUE",
        "CURLY_OPEN",
        "CURLY_CLOSE",
        "STARTUML",
        "ENDUML",
        "LEFT_ARROW",
        "RIGHT_ARROW",
        "BIDIRECT_ARROW",
        "PLAIN_LINE",
        "LINK_INFO",
    )

    identifier = r"[a-zA-Z_][0-9a-zA-Z_]*"
    # hex_digits = '[0-9a-fA-F]+'

    # character constants

    simple_escape = r"""(?:[a-zA-Z._~!=&\^\-\\?\'\"])"""
    byte_hex_escape = r"""(?:x[0-9a-fA-F][0-9a-fA-F])"""
    word_hex_escape = r"""(?:u[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F])"""
    hex_escape = byte_hex_escape + "|" + word_hex_escape
    escape = simple_escape + "|" + hex_escape
    bad_escape = r"(?:[\\](?!" + escape + ").)"
    simple_escape_sequence = r"""([\\]""" + simple_escape + ")"
    byte_hex_escape_sequence = r"""([\\]""" + byte_hex_escape + ")"
    word_hex_escape_sequence = r"""([\\]""" + word_hex_escape + ")"

    escape_sequence = r"""([\\](?:""" + escape + "))"

    # string literals and properties
    string_char = r"""(?:[^"\\\n]|""" + escape_sequence + ")"
    property_char = r"""(?:[^\\\n]|""" + escape_sequence + ")"
    bad_string_literal = '"' + string_char + "*(?:" + bad_escape + string_char + '*)*"'
    bad_property = "=>" + property_char + "*(?:" + bad_escape + property_char + "*)*\n"

    t_ignore = " \t"
    t_cppcomment_ignore = ""
    t_ccomment_ignore = ""
    t_strstate_ignore = ""
    t_propstate_ignore = ""
    t_lnkinfostate_ignore = ""

    t_CURLY_OPEN = r"{"
    t_CURLY_CLOSE = r"}"
    t_STARTUML = r"@startuml"
    t_ENDUML = r"@enduml"
    t_LEFT_ARROW = r"<-+"
    t_RIGHT_ARROW = r"-+>"
    t_BIDIRECT_ARROW = r"<-+>"
    t_PLAIN_LINE = r"-+"

    str_chars: list[str]

    def t_error(self, t: LexToken) -> None:
        self._error(
            _("Illegal character {char}, file {file}, line {line}, col {col}"),
            t,
            char=repr(t.value[0]),
        )  # pragma: no cover
        self.lexer.skip(1)  # pragma: no cover

    def t_CPPCOMMT(self, _: LexToken) -> None:
        r"""'"""
        self.lexer.begin("cppcomment")

    def t_cppcomment_NEWLINE(self, t: LexToken) -> None:
        r"""\n"""
        t.lexer.lineno += 1
        self.lexer.begin("INITIAL")

    def t_cppcomment_ALL(self, t: LexToken) -> None:
        r"""[^\n]+"""

    def t_cppcomment_error(self, t: LexToken) -> None:  # Should never happen
        self._error(
            _(
                "Illegal character in a C++-style comment: {char}, file {file}, line {line}, col {col}"
            ),
            t,
            char=repr(t.value[0]),
        )  # pragma: no cover
        self.lexer.skip(1)  # pragma: no cover

    def t_ccomment_error(self, t: LexToken) -> None:  # Should never happen
        self._error(
            _(
                "Illegal character in a C-style comment: {char}, file {file}, line {line}, col {col}"
            ),
            t,
            char=repr(t.value[0]),
        )  # pragma: no cover
        self.lexer.skip(1)  # pragma: no cover

    def t_strstate_error(self, t: LexToken) -> None:  # Should never happen
        self._error(
            _(
                "Illegal character in a string: {char}, file {file}, line {line}, col {col}"
            ),
            t,
            char=repr(t.value[0]),
        )  # pragma: no cover
        self.lexer.skip(1)  # pragma: no cover

    def t_TOSTR(self, t: LexToken) -> None:
        r"""\" """
        self.lexer.begin("strstate")
        self.str_chars = []
        self.str_pos = t.lexpos

    @TOKEN(bad_escape)
    def t_strstate_BAD_ESCAPE(self, t: LexToken) -> None:
        self._error(
            _("String contains an invalid escape code, {file}, line {line}, col {col}"),
            t,
        )
        self.str_chars.append(t.value[1])

    @TOKEN(byte_hex_escape_sequence)
    def t_strstate_BYTE_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0" + t.value[1:])))

    @TOKEN(word_hex_escape_sequence)
    def t_strstate_WORD_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0x" + t.value[2:])))

    @TOKEN(simple_escape_sequence)
    def t_strstate_SIMPLE_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(literal_eval("'" + t.value + "'"))

    def t_strstate_STR_SYMBOL(self, t: LexToken) -> None:
        """[^\"\\\n]"""
        self.str_chars.append(t.value)

    def t_strstate_STRING_LITERAL(self, t: LexToken) -> LexToken:
        r"""\" """
        t.lexpos = self.str_pos
        t.value = "".join(self.str_chars)
        self.lexer.begin("INITIAL")
        return t

    def t_strstate_NEWLINE(self, t: LexToken) -> LexToken:
        r"""\n"""
        t.lexer.lineno += 1
        t.lexpos = self.str_pos
        t.value = "".join(self.str_chars)
        self._error(
            _("An unclosed string literal found, {file}, line {line}, col {col}"), t
        )
        self.lexer.begin("INITIAL")
        t.type = "STRING_LITERAL"
        return t

    def t_propstate_error(self, t: LexToken) -> None:  # Should never happen
        # self._error(_('Illegal character in a property: {char}, file {file}, line {line}, col {col}'),
        #     t, char=repr(t.value[0])) #pragma: no cover
        return  # pragma: no cover

    def t_TOPROP(self, t: LexToken) -> None:
        r"""=>"""
        self.lexer.begin("propstate")
        self.str_chars = []
        self.str_pos = t.lexpos

    @TOKEN(bad_escape)
    def t_propstate_BAD_ESCAPE(self, t: LexToken) -> None:
        self._error(
            _(
                "Property contains an invalid escape code, {file}, line {line}, col {col}"
            ),
            t,
        )
        self.str_chars.append(t.value[1])

    @TOKEN(byte_hex_escape_sequence)
    def t_propstate_BYTE_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0" + t.value[1:])))

    @TOKEN(word_hex_escape_sequence)
    def t_propstate_WORD_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0x" + t.value[2:])))

    @TOKEN(simple_escape_sequence)
    def t_propstate_SIMPLE_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(literal_eval("'" + t.value + "'"))

    def t_propstate_STR_SYMBOL(self, t: LexToken) -> None:
        """[^\\\n]"""
        self.str_chars.append(t.value)

    def t_propstate_PROPERTY_VALUE(self, t: LexToken) -> LexToken:
        r"""\n"""
        t.lexer.lineno += 1
        t.lexpos = self.str_pos
        t.value = "".join(self.str_chars)
        if t.value.startswith(" ") or t.value.startswith("\t"):
            t.value = t.value[1:]
        self.lexer.begin("INITIAL")
        return t

    def t_lnkinfostate_error(self, t: LexToken) -> None:  # Should never happen
        # self._error(_('Illegal character in a property: {char}, file {file}, line {line}, col {col}'),
        #     t, char=repr(t.value[0])) #pragma: no cover
        return  # pragma: no cover

    def t_TOLNK(self, t: LexToken) -> None:
        r""":"""
        self.lexer.begin("lnkinfostate")
        self.str_chars = []
        self.str_pos = t.lexpos

    @TOKEN(bad_escape)
    def t_lnkinfostate_BAD_ESCAPE(self, t: LexToken) -> None:
        self._error(
            _(
                "Link info contains an invalid escape code, {file}, line {line}, col {col}"
            ),
            t,
        )
        self.str_chars.append(t.value[1])

    @TOKEN(byte_hex_escape_sequence)
    def t_lnkinfostate_BYTE_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0" + t.value[1:])))

    @TOKEN(word_hex_escape_sequence)
    def t_lnkinfostate_WORD_HEX_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(chr(literal_eval("0x" + t.value[2:])))

    @TOKEN(simple_escape_sequence)
    def t_lnkinfostate_SIMPLE_ESCAPE_SEQ(self, t: LexToken) -> None:
        self.str_chars.append(literal_eval("'" + t.value + "'"))

    def t_lnkinfostate_STR_SYMBOL(self, t: LexToken) -> None:
        """[^\\\n]"""
        self.str_chars.append(t.value)

    def t_lnkinfostate_LINK_INFO(self, t: LexToken) -> LexToken:
        r"""\n"""
        t.lexer.lineno += 1
        t.lexpos = self.str_pos
        t.value = "".join(self.str_chars)
        if t.value.startswith(" ") or t.value.startswith("\t"):
            t.value = t.value[1:]
        self.lexer.begin("INITIAL")
        return t

    def t_CCOMMT(self, _: LexToken) -> None:
        r"""/\'"""
        self.lexer.begin("ccomment")

    def t_ccomment_NEWLINE(self, t: LexToken) -> None:
        r"""\n"""
        t.lexer.lineno += 1

    def t_ccomment_END(self, _: LexToken) -> None:
        r"""\'/"""
        self.lexer.begin("INITIAL")

    def t_ccomment_ALL(self, t: LexToken) -> None:
        r"""[^\'\n]+"""

    def t_ccomment_AST(self, t: LexToken) -> None:
        r"""\'(?!/)"""

    def t_NEWLINE(self, t: LexToken) -> None:
        r"""\n+"""
        t.lexer.lineno += t.value.count("\n")

    @TOKEN(identifier)
    def t_ID(self, t: LexToken) -> LexToken:
        lowered = t.value.lower()
        if lowered not in self.keyword_map:
            t.type = "ID"
        else:
            t.type = t.value.upper()
            t.value = lowered
        # t.type = self.keyword_map.get(t.value, "ID").upper()
        return t
