from __future__ import annotations

import re
from dataclasses import dataclass

from .ast import BinOp, Const, Expr, Module, Not, Var


TOKEN_RE = re.compile(
    r"\s*(?:(?P<ID>[A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?)|"
    r"(?P<CONST>[0-9]+'[bB][01xXzZ]+|[01])|(?P<OP>[~&^|(),;=])|(?P<MISC>.+?))"
)


class VerilogParseError(ValueError):
    pass


def parse_verilog(source: str) -> Module:
    text = _strip_comments(source)
    module_match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*\((.*?)\)\s*;", text, re.S)
    if not module_match:
        raise VerilogParseError("missing module declaration")

    name = module_match.group(1)
    body_start = module_match.end()
    end_match = re.search(r"\bendmodule\b", text[body_start:], re.S)
    if not end_match:
        raise VerilogParseError("missing endmodule")
    body = text[body_start : body_start + end_match.start()]

    inputs: list[str] = []
    outputs: list[str] = []
    wires: list[str] = []
    assigns: dict[str, Expr] = {}

    for statement in _statements(body):
        if not statement:
            continue
        keyword = statement.split(None, 1)[0]
        if keyword in {"input", "output", "wire"}:
            names = _parse_declaration(statement)
            if keyword == "input":
                inputs.extend(names)
            elif keyword == "output":
                outputs.extend(names)
            else:
                wires.extend(names)
        elif keyword == "assign":
            target, expr = _parse_assign(statement)
            assigns[target] = expr
        else:
            raise VerilogParseError(f"unsupported statement: {statement}")

    if not inputs:
        raise VerilogParseError("module has no inputs")
    if not outputs:
        raise VerilogParseError("module has no outputs")

    return Module(
        name=name,
        inputs=_dedupe(inputs),
        outputs=_dedupe(outputs),
        wires=_dedupe(wires),
        assigns=assigns,
    )


def parse_file(path: str) -> Module:
    with open(path, "r", encoding="utf-8") as handle:
        return parse_verilog(handle.read())


def _strip_comments(source: str) -> str:
    source = re.sub(r"//.*?$", "", source, flags=re.M)
    return re.sub(r"/\*.*?\*/", "", source, flags=re.S)


def _statements(body: str) -> list[str]:
    return [part.strip() for part in body.split(";")]


def _parse_declaration(statement: str) -> list[str]:
    match = re.fullmatch(r"(input|output|wire)\s*(?:\[(\d+)\s*:\s*(\d+)\])?\s*(.+)", statement, re.S)
    if not match:
        raise VerilogParseError(f"bad declaration: {statement}")

    msb = match.group(2)
    lsb = match.group(3)
    raw_names = [name.strip() for name in match.group(4).split(",") if name.strip()]
    base_names = [_clean_decl_name(name) for name in raw_names]

    if msb is None:
        return base_names

    left = int(msb)
    right = int(lsb)
    step = 1 if right >= left else -1
    indices = range(left, right + step, step)
    return [f"{base}[{idx}]" for base in base_names for idx in indices]


def _clean_decl_name(name: str) -> str:
    cleaned = re.sub(r"\s+", "", name)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?", cleaned):
        raise VerilogParseError(f"bad signal name: {name}")
    return cleaned


def _parse_assign(statement: str) -> tuple[str, Expr]:
    match = re.fullmatch(r"assign\s+([A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?)\s*=\s*(.+)", statement, re.S)
    if not match:
        raise VerilogParseError(f"bad assign: {statement}")
    return match.group(1), ExpressionParser(tokenize(match.group(2))).parse()


def tokenize(expression: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    while position < len(expression):
        match = TOKEN_RE.match(expression, position)
        if not match:
            raise VerilogParseError(f"cannot tokenize expression near: {expression[position:]}")
        position = match.end()
        if match.group("ID") or match.group("CONST") or match.group("OP"):
            tokens.append(match.group(match.lastgroup))
        elif match.group("MISC").strip():
            raise VerilogParseError(f"invalid token: {match.group('MISC')}")
    return tokens


@dataclass
class ExpressionParser:
    tokens: list[str]
    pos: int = 0

    def parse(self) -> Expr:
        expr = self._parse_or()
        if self._peek() is not None:
            raise VerilogParseError(f"unexpected token: {self._peek()}")
        return expr

    def _parse_or(self) -> Expr:
        expr = self._parse_xor()
        while self._accept("|"):
            expr = BinOp("|", expr, self._parse_xor())
        return expr

    def _parse_xor(self) -> Expr:
        expr = self._parse_and()
        while self._accept("^"):
            expr = BinOp("^", expr, self._parse_and())
        return expr

    def _parse_and(self) -> Expr:
        expr = self._parse_unary()
        while self._accept("&"):
            expr = BinOp("&", expr, self._parse_unary())
        return expr

    def _parse_unary(self) -> Expr:
        if self._accept("~"):
            return Not(self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        token = self._peek()
        if token is None:
            raise VerilogParseError("unexpected end of expression")
        if self._accept("("):
            expr = self._parse_or()
            self._expect(")")
            return expr
        self.pos += 1
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*(?:\[[0-9]+\])?", token):
            return Var(token)
        if re.fullmatch(r"[01]", token):
            return Const(token == "1")
        const_match = re.fullmatch(r"\d+'[bB]([01xXzZ]+)", token)
        if const_match and len(const_match.group(1)) == 1 and const_match.group(1) in {"0", "1"}:
            return Const(const_match.group(1) == "1")
        raise VerilogParseError(f"unsupported constant or token: {token}")

    def _accept(self, token: str) -> bool:
        if self._peek() == token:
            self.pos += 1
            return True
        return False

    def _expect(self, token: str) -> None:
        if not self._accept(token):
            raise VerilogParseError(f"expected {token}, got {self._peek()}")

    def _peek(self) -> str | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
