from __future__ import annotations

from dataclasses import dataclass

from .cnf import CNF
from .netlist import Gate, Netlist, common_output_bits, load_yosys_json, validate_compatible_inputs
from .sat import solve
from .yosys_frontend import synthesize_to_json


@dataclass(frozen=True)
class SatOutputDiff:
    name: str
    differs: bool


@dataclass(frozen=True)
class SatEquivalenceResult:
    equivalent: bool
    outputs: list[SatOutputDiff]
    counterexample: dict[str, bool] | None
    solver: str
    variables: int
    clauses: int
    gates: int


def check_files_with_sat(golden_path: str, revised_path: str, solver: str = "auto") -> SatEquivalenceResult:
    golden = load_yosys_json(synthesize_to_json(golden_path))
    revised = load_yosys_json(synthesize_to_json(revised_path))
    return check_netlists_with_sat(golden, revised, solver=solver)


def check_netlists_with_sat(golden: Netlist, revised: Netlist, solver: str = "auto") -> SatEquivalenceResult:
    validate_compatible_inputs(golden, revised)
    compared_outputs = common_output_bits(golden, revised)

    cnf = CNF()
    cnf.constrain_constants()
    _alias_common_inputs(cnf, golden, revised)
    _encode_gates(cnf, "golden", golden.gates)
    _encode_gates(cnf, "revised", revised.gates)

    diff_lits: list[tuple[str, int]] = []
    for output_name, golden_bit, revised_bit in compared_outputs:
        diff = cnf.var(f"diff:{output_name}")
        cnf.add_xor(
            diff,
            cnf.lit_for_bit(golden_bit, "golden"),
            cnf.lit_for_bit(revised_bit, "revised"),
        )
        diff_lits.append((output_name, diff))

    cnf.add_clause(*(lit for _name, lit in diff_lits))
    solver_result = solve(cnf.clauses, len(cnf.var_ids), solver=solver)
    model = solver_result.model

    if model is None:
        return SatEquivalenceResult(
            equivalent=True,
            outputs=[SatOutputDiff(name, False) for name, _lit in diff_lits],
            counterexample=None,
            solver=solver_result.solver_used,
            variables=len(cnf.var_ids),
            clauses=len(cnf.clauses),
            gates=len(golden.gates) + len(revised.gates),
        )

    return SatEquivalenceResult(
        equivalent=False,
        outputs=[SatOutputDiff(name, model[lit]) for name, lit in diff_lits],
        counterexample=_counterexample(cnf, golden, model),
        solver=solver_result.solver_used,
        variables=len(cnf.var_ids),
        clauses=len(cnf.clauses),
        gates=len(golden.gates) + len(revised.gates),
    )


def _alias_common_inputs(cnf: CNF, golden: Netlist, revised: Netlist) -> None:
    for port in golden.inputs:
        for golden_bit, revised_bit in zip(golden.inputs[port], revised.inputs[port]):
            shared = cnf.var(f"input:{port}:{golden_bit}")
            _force_equal(cnf, cnf.lit_for_bit(golden_bit, "golden"), shared)
            _force_equal(cnf, cnf.lit_for_bit(revised_bit, "revised"), shared)


def _encode_gates(cnf: CNF, namespace: str, gates: list[Gate]) -> None:
    for gate in gates:
        output = cnf.lit_for_bit(gate.output, namespace)
        inputs = [cnf.lit_for_bit(bit, namespace) for bit in gate.inputs]
        if gate.type == "$_NOT_":
            cnf.add_not(output, inputs[0])
        elif gate.type == "$_AND_":
            cnf.add_and(output, inputs[0], inputs[1])
        elif gate.type == "$_OR_":
            cnf.add_or(output, inputs[0], inputs[1])
        elif gate.type == "$_XOR_":
            cnf.add_xor(output, inputs[0], inputs[1])
        else:
            raise ValueError(f"unsupported gate type: {gate.type}")


def _force_equal(cnf: CNF, left: int, right: int) -> None:
    cnf.add_clause(-left, right)
    cnf.add_clause(left, -right)


def _counterexample(cnf: CNF, golden: Netlist, model: dict[int, bool]) -> dict[str, bool]:
    assignment: dict[str, bool] = {}
    for port_bit in golden.input_bits:
        lit = cnf.lit_for_bit(port_bit.bit, "golden")
        assignment[port_bit.name] = model[abs(lit)] == (lit > 0)
    return assignment
