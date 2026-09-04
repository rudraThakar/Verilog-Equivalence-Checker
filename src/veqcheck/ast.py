from __future__ import annotations

from dataclasses import dataclass


class Expr:
    pass


@dataclass(frozen=True)
class Var(Expr):
    name: str


@dataclass(frozen=True)
class Const(Expr):
    value: bool


@dataclass(frozen=True)
class Not(Expr):
    operand: Expr


@dataclass(frozen=True)
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Module:
    name: str
    inputs: list[str]
    outputs: list[str]
    wires: list[str]
    assigns: dict[str, Expr]
