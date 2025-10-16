from __future__ import annotations
from typing import cast, TYPE_CHECKING, Protocol, Optional, Any, List, Union

from pc.astree.ast import AstNode

if not TYPE_CHECKING:
    import ply.yacc

    yacc, YaccProduction = ply.yacc.yacc, ply.yacc.YaccProduction
else:
    from pc.lexer.plylex_types import LexToken

    class YaccParserProtocol(Protocol):
        def parse(
            self, input: str, lexer: Optional[Any] = None, debug: int = 0
        ) -> AstNode: ...
        def error(self, token: LexToken) -> None: ...

    def yacc(
        module: Any,
        start: str,
        debug: Any,
        optimize: Any,
        write_tables: Any,
        tabmodule: Any = None,
    ) -> YaccParserProtocol:
        return cast(YaccParserProtocol, None)

    class YaccProduction(Protocol):
        slice: List[LexToken]

        def __getitem__(self, index: int) -> Union[AstNode, str]: ...
        def __setitem__(self, index: int, value: Union[AstNode, str]) -> None: ...
        def __len__(self) -> int: ...
