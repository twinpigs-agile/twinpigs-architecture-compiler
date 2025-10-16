# REGISTER_DOCTEST
from io import StringIO
from typing import Callable, Any, Tuple, Dict, Iterator


def ignore_exceptions(
    c: Callable[..., Any], *a: Tuple[Any], **kw: Dict[str, Any]
) -> Any:
    """
    >>> def thrower(*aa, **kkw):
    ...     raise Exception()
    >>> def nothrower(*aa, **kkw):
    ...     return ':'.join((':'.join(aa), ':'.join(kkw.keys()), ':'.join(kkw.values())))
    >>> ignore_exceptions(thrower, 0, a=1)
    >>> ignore_exceptions(nothrower, '0', a='1')
    '0:a:1'
    """
    # noinspection PyBroadException
    try:
        return c(*a, **kw)
    except Exception:
        pass


class TestIO(StringIO):
    """
    >>> tio = TestIO(); (None, tio.write('a\\rb'))[0]; tio.getvalue()
    'ab'
    """

    def getvalue(self) -> str:
        return StringIO.getvalue(self).replace("\r", "")


def iter_dict_lexorder(d: Dict[str, Any]) -> Iterator[Tuple[str, Any]]:
    """
    >>> [i for i in iter_dict_lexorder({'a': 1, 'b': 2, 'c': 3})] # type: ignore
    [('a', 1), ('b', 2), ('c', 3)]
    >>> [i for i in iter_dict_lexorder({'b': 2, 'c': 3, 'a': 1})] # type: ignore
    [('a', 1), ('b', 2), ('c', 3)]
    """
    kl = list(d.keys())
    kl.sort()
    for k in kl:
        yield k, d[k]


class KeyValue(object):
    """
    >>> kv = KeyValue(a=1, b=2)
    >>> kv.a, kv.b
    (1, 2)
    """

    def __init__(self, **kw: Any):
        self.__kvalues = {}
        for k, v in kw.items():
            self.__kvalues[k] = v

    def __getattr__(self, k: str) -> Any:
        if k in self.__kvalues:
            return self.__kvalues[k]
        raise AttributeError(f"{k} not found in {self.__class__.__name__}")
