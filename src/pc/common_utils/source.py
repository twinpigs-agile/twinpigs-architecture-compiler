# REGISTER_DOCTEST
from bisect import bisect
import hashlib
from typing import Tuple, Optional


class PositionDecoder(object):
    """
    >>> pd = PositionDecoder(""); pd.get_lc(0), pd.get_lc(1)
    ((1, 1), (1, 2))
    >>> pd = PositionDecoder("a\\nb\\nc"); [pd.get_lc(i) for i in range(7)] # type: ignore
    [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2), (3, 3)]
    """

    def __init__(self, text: str):
        ll = [len(t) + 1 for t in text.split("\n")]
        ln = 0
        self.pos_list = [0]
        for i in ll:
            self.pos_list.append(ln)
            ln += i
        del self.pos_list[0]

    def get_lc(self, pos: int) -> Tuple[int, int]:
        ln = max(bisect(self.pos_list, pos) - 1, 0)
        c = pos - self.pos_list[ln]
        return ln + 1, c + 1


class Source(object):
    """
    >>> s1 = Source("Line1\\nLine2"); s2 = Source("Line01\\nLine02")
    >>> s1.hash != s2.hash
    True
    >>> [s1.get_lc(i) for i in range(len(s1.text))]  # type: ignore
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5)]
    >>> [s2.get_lc(i) for i in range(len(s2.text))]  # type: ignore
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]
    """

    def __init__(
        self, text: str, module: Optional[str] = None, path: Optional[str] = None
    ) -> None:
        self.module, self.path = module, path
        self.text = text.replace("\r", "")
        self.pos_decoder = PositionDecoder(self.text)
        h = hashlib.new("SHA256")
        h.update(self.text.encode("utf8"))
        self.hash = h.hexdigest()

    def get_lc(self, pos: int) -> Tuple[int, int]:
        return self.pos_decoder.get_lc(pos)
