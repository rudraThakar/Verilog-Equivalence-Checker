from __future__ import annotations


class CNF:
    def __init__(self):
        self.var_ids: dict[str, int] = {}
        self.names: dict[int, str] = {}
        self.clauses: list[list[int]] = []

    def var(self, name: str) -> int:
        if name not in self.var_ids:
            idx = len(self.var_ids) + 1
            self.var_ids[name] = idx
            self.names[idx] = name
        return self.var_ids[name]

    def lit_for_bit(self, bit: str, namespace: str) -> int:
        if bit == "0":
            return -self.var("__const_true")
        if bit == "1":
            return self.var("__const_true")
        return self.var(f"{namespace}:{bit}")

    def add_clause(self, *lits: int) -> None:
        self.clauses.append(list(lits))

    def force_true(self, lit: int) -> None:
        self.add_clause(lit)

    def constrain_constants(self) -> None:
        self.force_true(self.var("__const_true"))

    def add_not(self, y: int, a: int) -> None:
        self.add_clause(-a, -y)
        self.add_clause(a, y)

    def add_and(self, y: int, a: int, b: int) -> None:
        self.add_clause(-a, -b, y)
        self.add_clause(a, -y)
        self.add_clause(b, -y)

    def add_or(self, y: int, a: int, b: int) -> None:
        self.add_clause(a, b, -y)
        self.add_clause(-a, y)
        self.add_clause(-b, y)

    def add_xor(self, y: int, a: int, b: int) -> None:
        self.add_clause(-a, -b, -y)
        self.add_clause(-a, b, y)
        self.add_clause(a, -b, y)
        self.add_clause(a, b, -y)
