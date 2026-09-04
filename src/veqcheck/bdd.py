from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable


FALSE = 0
TRUE = 1


@dataclass(frozen=True)
class Node:
    var: str
    low: int
    high: int


class BDDManager:
    def __init__(self, variable_order: list[str]):
        self.variable_order = variable_order
        self.level = {name: index for index, name in enumerate(variable_order)}
        self.nodes: list[Node | None] = [None, None]
        self.unique: dict[tuple[str, int, int], int] = {}

    def const(self, value: bool) -> int:
        return TRUE if value else FALSE

    def var(self, name: str) -> int:
        if name not in self.level:
            raise KeyError(f"unknown BDD variable: {name}")
        return self.mk(name, FALSE, TRUE)

    def mk(self, var: str, low: int, high: int) -> int:
        if low == high:
            return low
        key = (var, low, high)
        if key in self.unique:
            return self.unique[key]
        node_id = len(self.nodes)
        self.nodes.append(Node(var, low, high))
        self.unique[key] = node_id
        return node_id

    def negate(self, root: int) -> int:
        return self.apply(lambda a, _b: not a, root, FALSE)

    def land(self, left: int, right: int) -> int:
        return self.apply(lambda a, b: a and b, left, right)

    def lor(self, left: int, right: int) -> int:
        return self.apply(lambda a, b: a or b, left, right)

    def xor(self, left: int, right: int) -> int:
        return self.apply(lambda a, b: a != b, left, right)

    def apply(self, op: Callable[[bool, bool], bool], left: int, right: int) -> int:
        @lru_cache(maxsize=None)
        def rec(a: int, b: int) -> int:
            if a in (FALSE, TRUE) and b in (FALSE, TRUE):
                return self.const(op(a == TRUE, b == TRUE))

            top_var = self._top_var(a, b)
            a_low, a_high = self._cofactor(a, top_var)
            b_low, b_high = self._cofactor(b, top_var)
            return self.mk(top_var, rec(a_low, b_low), rec(a_high, b_high))

        return rec(left, right)

    def difference(self, left: int, right: int) -> int:
        return self.xor(left, right)

    def counterexample(self, root: int) -> dict[str, bool] | None:
        if root == FALSE:
            return None
        assignment: dict[str, bool] = {}
        current = root
        while current not in (FALSE, TRUE):
            node = self._node(current)
            if node.high != FALSE:
                assignment[node.var] = True
                current = node.high
            else:
                assignment[node.var] = False
                current = node.low
        if current == TRUE:
            for variable in self.variable_order:
                assignment.setdefault(variable, False)
            return assignment
        return None

    def node_count(self) -> int:
        return max(0, len(self.nodes) - 2)

    def _top_var(self, left: int, right: int) -> str:
        candidates = []
        if left not in (FALSE, TRUE):
            candidates.append(self._node(left).var)
        if right not in (FALSE, TRUE):
            candidates.append(self._node(right).var)
        return min(candidates, key=lambda name: self.level[name])

    def _cofactor(self, root: int, variable: str) -> tuple[int, int]:
        if root in (FALSE, TRUE):
            return root, root
        node = self._node(root)
        if node.var == variable:
            return node.low, node.high
        return root, root

    def _node(self, node_id: int) -> Node:
        node = self.nodes[node_id]
        if node is None:
            raise ValueError("terminal node has no variable")
        return node
