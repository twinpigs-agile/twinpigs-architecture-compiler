import re
from typing import Union, Optional, cast, Callable
from os.path import sep

from pc.lexer.plylex_types import LexToken
from pc.parser.plyparse_types import yacc, YaccProduction

from pc.errorlog.error import StackedErrorContext, Severity
from pc.astree.ast import AstNode, SourceRef
from pc.lexer.lexer import Lexer
from pc.common_utils.source import Source
import pc.settings.settings
from pc.settings.settings import YACC_DEBUG, YACC_OPTIMIZE, LEX_OPTIMIZE, PARSE_DEBUG

_ = cast(Callable[[str], str], getattr(pc.settings.settings, "_"))


class Parser:
    GROUP_TYPES = {
        "rectangle": "group",
        "computer": "computer",
        "vm": "vm",
        "group": "group",
        "container": "container",
        "containers": "containers",
        "external": "external",
        "service": "service",
    }

    def _get_group_type(self, keyword: str) -> str:
        return self.GROUP_TYPES[keyword]

    def p_error(self, p: Optional[LexToken]) -> None:
        if isinstance(p, LexToken):
            sref = self._srcref(p)
            self.error_context.fix(
                Severity.ERROR,
                _("Syntax error near {v}, {f}, line {l}, col {c}"),
                v=repr(p.value),
                f=sref.f,
                l=sref.ln,
                c=sref.col,
            )
        else:
            self.error_context.fix(
                Severity.ERROR, _('Syntax error at the end of "{f}"'), f=self.src_file
            )  # pragma: no cover

    def _srcref(self, token: Optional[Union[LexToken, AstNode]] = None) -> SourceRef:
        if token:
            if isinstance(token, AstNode):
                return token.src_ref
            return SourceRef(self.src_file, *self.source_obj.get_lc(token.lexpos))  # type: ignore
        return SourceRef(self.src_file, None, None)

    def __init__(
        self,
        src_file: str,
        error_context: Optional[StackedErrorContext] = None,
        lex_optimize: int = LEX_OPTIMIZE,
        # lextab='pycparser.lextab',
        yacc_optimize: int = YACC_OPTIMIZE,
        # yacctab='pycparser.yacctab',
        yacc_debug: int = YACC_DEBUG,
    ):
        self.error_context: StackedErrorContext = error_context or StackedErrorContext()
        self.src_file = src_file.replace(sep, "/").replace("\\", "/")

        self.lex = Lexer(self.error_context, src_file)

        self.lex.build(optimize=lex_optimize, lextab="")  # ,
        # lextab=lextab)
        self.tokens = self.lex.tokens

        self.parser = yacc(
            module=self,
            start="puml",
            debug=yacc_debug,
            optimize=yacc_optimize,
            write_tables=yacc_debug,  # ,
            # tabmodule=yacctab
        )

    def parse(self, text: str, debuglevel: int = PARSE_DEBUG) -> Optional[AstNode]:
        """Returns AST"""
        self.source_obj = Source(text)
        self.lex.source_obj = self.source_obj
        res = self.parser.parse(self.source_obj.text, lexer=self.lex, debug=debuglevel)
        if self.error_context.max_severity > Severity.WARNING:
            return None
        return res

    def p_puml(self, p: YaccProduction) -> None:
        """puml : real_puml
        | empty_puml
        """
        p[0] = p[1]

    def p_real_puml(self, p: YaccProduction) -> None:
        """real_puml : STARTUML definitions ENDUML"""
        p[0] = AstNode(
            "puml",
            self._srcref(),
            children=cast(AstNode, p[2]).children,
            hash=self.source_obj.hash,
            file=self.src_file,
        )

    def p_empty_puml(self, p: YaccProduction) -> None:
        """empty_puml : STARTUML ENDUML"""
        p[0] = AstNode(
            "puml", self._srcref(), hash=self.source_obj.hash, file=self.src_file
        )

    def p_definitions(self, p: YaccProduction) -> None:
        """definitions : definition
        | definitions definition
        | definitions link_definition
        """
        if len(p) == 2:
            p[0] = AstNode(
                "definitions",
                src_ref=self._srcref(cast(AstNode, p[1])),
                children=[cast(AstNode, p[1])],
            )
        else:
            p[0] = AstNode(
                "definitions",
                src_ref=self._srcref(cast(AstNode, p[1])),
                children=cast(AstNode, p[1]).children + [cast(AstNode, p[2])],
            )

    def p_definition(self, p: YaccProduction) -> None:
        """definition : map_aliased
        | map_unaliased
        | rectangle_aliased
        | rectangle_unaliased
        """
        p[0] = p[1]

    id_prohibited_pattern = re.compile(r"[\n\t]")
    name_prohibited_pattern = id_prohibited_pattern

    def _check_id(self, id: LexToken) -> None:
        msg = None
        if id.value.startswith(" ") or id.value.endswith(" "):
            msg = _(
                "An item ID should not start or end with whitespace! ID: {v}, file {f}, line {l}, col {c}"
            )
        elif self.id_prohibited_pattern.search(id.value):
            msg = _(
                "Illegal symbols found in an item ID! ID: {v}, file {f}, line {l}, col {c}"
            )
        if msg:
            sref = self._srcref(id)
            self.error_context.fix(
                Severity.ERROR, msg, v=repr(id.value), f=sref.f, l=sref.ln, c=sref.col
            )

    def _check_name(self, name: LexToken) -> None:
        msg = None
        if self.name_prohibited_pattern.search(name.value):
            msg = _(
                "Illegal symbols found in an item name! Name: {v}, file {f}, line {l}, col {c}"
            )
        if msg:
            sref = self._srcref(name)
            self.error_context.fix(
                Severity.ERROR, msg, v=repr(name.value), f=sref.f, l=sref.ln, c=sref.col
            )

    def p_map_aliased(self, p: YaccProduction) -> None:
        """map_aliased : MAP STRING_LITERAL AS ID properties CURLY_CLOSE
        | SERVICE STRING_LITERAL AS ID properties CURLY_CLOSE
        """
        p[0] = p[1]
        name, id = p.slice[2].value, p.slice[4].value
        self._check_id(p.slice[4])
        self._check_name(p.slice[2])
        p[0] = AstNode(
            "map",
            self._srcref(p.slice[1]),
            id=id,
            name=name,
            children=cast(AstNode, p[5]).children,
        )

    def p_map_unaliased(self, p: YaccProduction) -> None:
        """map_unaliased : MAP ID properties CURLY_CLOSE
        | SERVICE ID properties CURLY_CLOSE
        | MAP STRING_LITERAL properties CURLY_CLOSE
        | SERVICE STRING_LITERAL properties CURLY_CLOSE
        """
        p[0] = p[1]
        name, id = p.slice[2].value, p.slice[2].value
        self._check_id(p.slice[2])
        p[0] = AstNode(
            "map",
            self._srcref(p.slice[1]),
            id=id,
            name=name,
            children=cast(AstNode, p[3]).children,
        )

    def p_empty_properties(self, p: YaccProduction) -> None:
        """empty_properties : CURLY_OPEN"""
        p[0] = AstNode("properties", self._srcref(p.slice[1]), children=[])

    def p_properties(self, p: YaccProduction) -> None:
        """properties : empty_properties
        | properties property
        """
        p[0] = p[1]
        if len(p) > 2:
            cast(AstNode, p[0]).children = cast(AstNode, p[0]).children + [
                cast(AstNode, p[2])
            ]

    def p_property(self, p: YaccProduction) -> None:
        """property : ID PROPERTY_VALUE"""
        self._check_id(p.slice[1])
        p[0] = AstNode("property", self._srcref(p.slice[1]), id=p[1], value=p[2])

    def p_empty_rect_insides(self, p: YaccProduction) -> None:
        """empty_rect_insides : CURLY_OPEN"""
        p[0] = AstNode("rect_insides", self._srcref(p.slice[1]), children=[])

    def p_rect_insides(self, p: YaccProduction) -> None:
        """rect_insides : empty_rect_insides
        | rect_insides definition
        """
        p[0] = p[1]
        if len(p) > 2:
            cast(AstNode, p[0]).children = cast(AstNode, p[0]).children + [
                cast(AstNode, p[2])
            ]

    def p_rectangle_aliased(self, p: YaccProduction) -> None:
        """rectangle_aliased : RECTANGLE STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | GROUP STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | CONTAINER STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | COMPUTER STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | VM STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | CONTAINERS STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        | EXTERNAL STRING_LITERAL AS ID rect_insides CURLY_CLOSE
        """
        p[0] = p[1]
        name, id = p.slice[2].value, p.slice[4].value
        self._check_id(p.slice[2])
        self._check_name(p.slice[4])
        p[0] = AstNode(
            "rectangle",
            self._srcref(p.slice[1]),
            id=id,
            name=name,
            group_type=self._get_group_type(p.slice[1].value),
            children=cast(AstNode, p[5]).children,
        )

    def p_rectangle_unaliased(self, p: YaccProduction) -> None:
        """rectangle_unaliased : RECTANGLE ID rect_insides CURLY_CLOSE
        | GROUP ID rect_insides CURLY_CLOSE
        | CONTAINER ID rect_insides CURLY_CLOSE
        | CONTAINERS ID rect_insides CURLY_CLOSE
        | COMPUTER ID rect_insides CURLY_CLOSE
        | VM ID rect_insides CURLY_CLOSE
        | EXTERNAL ID rect_insides CURLY_CLOSE
        | SERVICE ID rect_insides CURLY_CLOSE
        | RECTANGLE STRING_LITERAL rect_insides CURLY_CLOSE
        | GROUP STRING_LITERAL rect_insides CURLY_CLOSE
        | CONTAINER STRING_LITERAL rect_insides CURLY_CLOSE
        | CONTAINERS STRING_LITERAL rect_insides CURLY_CLOSE
        | COMPUTER STRING_LITERAL rect_insides CURLY_CLOSE
        | VM STRING_LITERAL rect_insides CURLY_CLOSE
        | EXTERNAL STRING_LITERAL rect_insides CURLY_CLOSE
        """
        p[0] = p[1]
        name, id = p.slice[2].value, p.slice[2].value
        self._check_id(p.slice[2])
        p[0] = AstNode(
            "rectangle",
            self._srcref(p.slice[1]),
            id=id,
            name=name,
            group_type=self._get_group_type(p.slice[1].value),
            children=cast(AstNode, p[3]).children,
        )

    def p_link_sign(self, p: YaccProduction) -> None:
        """link_sign : LEFT_ARROW
        | RIGHT_ARROW
        | BIDIRECT_ARROW
        | PLAIN_LINE
        """
        p[0] = p.slice[1].type

    def p_link_definition(self, p: YaccProduction) -> None:
        """link_definition : ID link_sign ID LINK_INFO
        | ID link_sign ID
        | ID link_sign STRING_LITERAL LINK_INFO
        | ID link_sign STRING_LITERAL
        | STRING_LITERAL link_sign STRING_LITERAL LINK_INFO
        | STRING_LITERAL link_sign STRING_LITERAL
        | STRING_LITERAL link_sign ID LINK_INFO
        | STRING_LITERAL link_sign ID"""
        info = None
        if len(p) > 4:
            info = p[4]
        self._check_id(p.slice[1])
        self._check_id(p.slice[3])
        _1to2 = p[2] in ("RIGHT_ARROW", "BIDIRECT_ARROW")
        _2to1 = p[2] in ("LEFT_ARROW", "BIDIRECT_ARROW")
        # NB: PLAIN_LINE means both are set to False
        p[0] = AstNode(
            "link",
            self._srcref(p.slice[1]),
            id1=p[1],
            id2=p[3],
            _1to2=_1to2,
            _2to1=_2to1,
            info=info,
        )
