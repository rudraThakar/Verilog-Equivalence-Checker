from __future__ import annotations

from dataclasses import dataclass

from .ast import BinOp, Const, Expr, Module, Not, Var
from .bdd import BDDManager, FALSE


@dataclass(frozen=True)
class OutputResult:
    name: str
    equivalent: bool
    counterexample: dict[str, bool] | None = None


@dataclass(frozen=True)
class EquivalenceResult:
    equivalent: bool
    outputs: list[OutputResult]
    node_count: int


class BuildError(ValueError):
    pass


def check_equivalence(left: Module, right: Module) -> EquivalenceResult:
    outputs = sorted(set(left.outputs) & set(right.outputs), key=_signal_sort_key)
    if not outputs:
        raise BuildError("modules have no common outputs to compare")

    inputs = sorted(set(left.inputs) | set(right.inputs), key=_signal_sort_key)
    manager = BDDManager(inputs)
    left_builder = BDDBuilder(left, manager)
    right_builder = BDDBuilder(right, manager)

    results: list[OutputResult] = []
    for output in outputs:
        left_root = left_builder.build_signal(output)
        right_root = right_builder.build_signal(output)
        diff = manager.difference(left_root, right_root)
        results.append(
            OutputResult(
                name=output,
                equivalent=diff == FALSE,
                counterexample=None if diff == FALSE else manager.counterexample(diff),
            )
        )

    return EquivalenceResult(
        equivalent=all(result.equivalent for result in results),
        outputs=results,
        node_count=manager.node_count(),
    )


class BDDBuilder:
    def __init__(self, module: Module, manager: BDDManager):
        self.module = module
        self.manager = manager
        self.cache: dict[str, int] = {}
        self.active: set[str] = set()

    def build_signal(self, name: str) -> int:
        if name in self.cache:
            return self.cache[name]
        if name in self.module.inputs:
            root = self.manager.var(name)
        elif name in self.module.assigns:
            if name in self.active:
                raise BuildError(f"combinational cycle detected at {name}")
            self.active.add(name)
            root = self.build_expr(self.module.assigns[name])
            self.active.remove(name)
        else:
            raise BuildError(f"{self.module.name}: signal {name} is not driven")
        self.cache[name] = root
        return root

    def build_expr(self, expr: Expr) -> int:
        if isinstance(expr, Const):
            return self.manager.const(expr.value)
        if isinstance(expr, Var):
            return self.build_signal(expr.name)
        if isinstance(expr, Not):
            return self.manager.negate(self.build_expr(expr.operand))
        if isinstance(expr, BinOp):
            left = self.build_expr(expr.left)
            right = self.build_expr(expr.right)
            if expr.op == "&":
                return self.manager.land(left, right)
            if expr.op == "|":
                return self.manager.lor(left, right)
            if expr.op == "^":
                return self.manager.xor(left, right)
        raise BuildError(f"unsupported expression: {expr!r}")


def _signal_sort_key(name: str) -> tuple[str, int]:
    if "[" in name and name.endswith("]"):
        base, index = name[:-1].split("[", 1)
        return base, int(index)
    return name, -1
