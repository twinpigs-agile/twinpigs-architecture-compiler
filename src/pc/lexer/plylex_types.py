from __future__ import annotations
from typing import (
    cast,
    Callable,
    Any,
    Protocol,
    Optional,
    Iterator,
    TYPE_CHECKING,
    runtime_checkable,
)

if not TYPE_CHECKING:
    import ply.lex as lex

    TOKEN, LexToken = lex.TOKEN, lex.LexToken
else:

    class LexModule(Protocol):
        def lex(self, object: Any, **kw: Any) -> LexerProtocol: ...

    lex: LexModule = cast(LexModule, None)

    class LexerProtocol(Protocol):
        lineno: int
        lexpos: int

        def input(self, data: str) -> None: ...
        def begin(self, _: str) -> None: ...
        def token(self) -> Optional[LexToken]: ...
        def clone(self) -> LexerProtocol: ...
        def __iter__(self) -> Iterator[Any]: ...
        def __next__(self) -> Any: ...
        def skip(self, n: int) -> None: ...
        def current_state(self) -> str: ...

    @runtime_checkable
    class LexToken(Protocol):
        type: str
        value: Any
        lineno: int
        lexpos: int
        lexer: LexerProtocol

    def TOKEN(  # type:ignore
        _: str,
    ) -> Callable[
        [Callable[[Any, LexToken], Optional[LexToken]]],
        Callable[[Any, LexToken], Optional[LexToken]],
    ]: ...
