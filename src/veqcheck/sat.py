from __future__ import annotations

from dataclasses import dataclass


SolverName = str


class SolverUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SolverResult:
    model: dict[int, bool] | None
    solver_used: str


def solve(clauses: list[list[int]], num_vars: int, solver: SolverName = "auto") -> SolverResult:
    if solver == "dpll":
        return SolverResult(solve_dpll(clauses, num_vars), "dpll")
    if solver not in {"auto", "glucose"}:
        raise ValueError(f"unknown SAT solver: {solver}")

    pysat_result = _solve_with_pysat(clauses, num_vars)
    if pysat_result is not _PYSAT_UNAVAILABLE:
        return SolverResult(pysat_result, "glucose")
    if solver == "glucose":
        raise SolverUnavailable("PySAT/Glucose3 is not installed")
    return SolverResult(solve_dpll(clauses, num_vars), "dpll")


_PYSAT_UNAVAILABLE = object()


def _solve_with_pysat(clauses: list[list[int]], num_vars: int) -> dict[int, bool] | None | object:
    try:
        from pysat.solvers import Glucose3
    except ImportError:
        return _PYSAT_UNAVAILABLE

    with Glucose3(bootstrap_with=clauses) as solver:
        if not solver.solve():
            return None
        model = solver.get_model()

    assignment = {abs(lit): lit > 0 for lit in model}
    for var in range(1, num_vars + 1):
        assignment.setdefault(var, False)
    return assignment


def solve_dpll(clauses: list[list[int]], num_vars: int) -> dict[int, bool] | None:
    assignment: dict[int, bool] = {}
    result = _dpll([clause[:] for clause in clauses], assignment, num_vars)
    if result is None:
        return None
    for var in range(1, num_vars + 1):
        result.setdefault(var, False)
    return result


def _dpll(clauses: list[list[int]], assignment: dict[int, bool], num_vars: int) -> dict[int, bool] | None:
    while True:
        simplified = _simplify(clauses, assignment)
        if simplified is None:
            return None
        clauses = simplified
        if not clauses:
            return assignment

        unit = next((clause[0] for clause in clauses if len(clause) == 1), None)
        if unit is not None:
            if not _assign(assignment, abs(unit), unit > 0):
                return None
            continue

        pure = _find_pure_literal(clauses, assignment)
        if pure is not None:
            if not _assign(assignment, abs(pure), pure > 0):
                return None
            continue

        break

    variable = _choose_variable(clauses, assignment, num_vars)
    if variable is None:
        return assignment

    for value in (True, False):
        branch = assignment.copy()
        branch[variable] = value
        solved = _dpll(clauses, branch, num_vars)
        if solved is not None:
            return solved
    return None


def _simplify(clauses: list[list[int]], assignment: dict[int, bool]) -> list[list[int]] | None:
    simplified: list[list[int]] = []
    for clause in clauses:
        new_clause: list[int] = []
        satisfied = False
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                new_clause.append(lit)
            elif assignment[var] == (lit > 0):
                satisfied = True
                break
        if satisfied:
            continue
        if not new_clause:
            return None
        simplified.append(new_clause)
    return simplified


def _assign(assignment: dict[int, bool], variable: int, value: bool) -> bool:
    existing = assignment.get(variable)
    if existing is not None:
        return existing == value
    assignment[variable] = value
    return True


def _find_pure_literal(clauses: list[list[int]], assignment: dict[int, bool]) -> int | None:
    polarity: dict[int, int] = {}
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            if var in assignment:
                continue
            sign = 1 if lit > 0 else -1
            polarity[var] = sign if var not in polarity else (polarity[var] if polarity[var] == sign else 0)
    for var, sign in polarity.items():
        if sign:
            return var if sign > 0 else -var
    return None


def _choose_variable(clauses: list[list[int]], assignment: dict[int, bool], num_vars: int) -> int | None:
    counts: dict[int, int] = {}
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                counts[var] = counts.get(var, 0) + 1
    if counts:
        return max(counts, key=counts.get)
    for var in range(1, num_vars + 1):
        if var not in assignment:
            return var
    return None
