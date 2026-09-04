from __future__ import annotations

import argparse
import sys

from .equivalence import BuildError, check_equivalence
from .parser import VerilogParseError, parse_file
from .sat_equivalence import check_files_with_sat
from .sat import SolverUnavailable
from .yosys_frontend import YosysError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Combinational Verilog equivalence checker")
    parser.add_argument("golden", help="golden/reference Verilog file")
    parser.add_argument("revised", help="revised Verilog file")
    parser.add_argument(
        "--backend",
        choices=["sat", "bdd"],
        default="sat",
        help="sat uses Yosys JSON plus this project's CNF/SAT engine; bdd uses the educational built-in parser",
    )
    parser.add_argument(
        "--solver",
        choices=["auto", "glucose", "dpll"],
        default="auto",
        help="SAT solver for --backend sat: glucose uses PySAT/Glucose3, dpll uses this project's own solver",
    )
    parser.add_argument("--show-all", action="store_true", help="print every compared output")
    args = parser.parse_args(argv)

    if args.backend == "sat":
        return _run_sat_backend(args.golden, args.revised, args.show_all, args.solver)
    return _run_bdd_backend(args.golden, args.revised, args.show_all)


def _run_sat_backend(golden_path: str, revised_path: str, show_all: bool, solver: str) -> int:
    try:
        result = check_files_with_sat(golden_path, revised_path, solver=solver)
    except (YosysError, ValueError, SolverUnavailable, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if result.equivalent:
        print("EQUIVALENT")
        print("Backend: Yosys frontend + project SAT miter")
        print(f"SAT solver: {result.solver}")
        print("Compared outputs: " + ", ".join(output.name for output in result.outputs))
        print(f"Gates encoded: {result.gates}")
        print(f"CNF: {result.variables} variables, {result.clauses} clauses")
        return 0

    print("NOT EQUIVALENT")
    print("Backend: Yosys frontend + project SAT miter")
    print(f"SAT solver: {result.solver}")
    for output in result.outputs:
        if output.differs:
            print(f"Output {output.name} differs.")
        elif show_all:
            print(f"Output {output.name}: no difference in returned model")
    print("Counterexample:")
    for name, value in sorted(result.counterexample.items(), key=lambda item: _signal_sort_key(item[0])):
        print(f"  {name} = {int(value)}")
    print(f"Gates encoded: {result.gates}")
    print(f"CNF: {result.variables} variables, {result.clauses} clauses")
    return 1


def _run_bdd_backend(golden_path: str, revised_path: str, show_all: bool) -> int:
    try:
        golden = parse_file(golden_path)
        revised = parse_file(revised_path)
        result = check_equivalence(golden, revised)
    except (OSError, VerilogParseError, BuildError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if result.equivalent:
        print("EQUIVALENT")
        print("Compared outputs: " + ", ".join(output.name for output in result.outputs))
        print(f"BDD nodes: {result.node_count}")
        return 0

    print("NOT EQUIVALENT")
    for output in result.outputs:
        if output.equivalent and show_all:
            print(f"Output {output.name}: equivalent")
        if not output.equivalent:
            print(f"Output {output.name} differs.")
            print("Counterexample:")
            for name, value in sorted(output.counterexample.items(), key=lambda item: _signal_sort_key(item[0])):
                print(f"  {name} = {int(value)}")
            break
    print(f"BDD nodes: {result.node_count}")
    return 1


def _signal_sort_key(name: str) -> tuple[str, int]:
    if "[" in name and name.endswith("]"):
        base, index = name[:-1].split("[", 1)
        return base, int(index)
    return name, -1


if __name__ == "__main__":
    raise SystemExit(main())
