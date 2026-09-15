# Verilog Equivalence Checker

A SAT-based combinational equivalence checker for Verilog designs.

This project compares two implementations of the same combinational circuit and determines whether they produce identical outputs for every possible input assignment. It uses Yosys as the Verilog frontend and implements the equivalence-checking flow in Python: netlist loading, miter construction, CNF generation, SAT solving, and counterexample reporting.

## What It Does

Given two Verilog files:

```text
golden.v   -> reference implementation
revised.v  -> optimized, refactored, or modified implementation
```

the tool answers:

```text
Is there any input combination where the two designs produce different outputs?
```

If such an input exists, the designs are reported as **not equivalent**, and the tool prints a concrete counterexample. If no such input exists, the designs are reported as **equivalent**.

## Features

- Verilog frontend powered by Yosys.
- Gate-level netlist extraction from Yosys JSON.
- SAT miter construction across matching output bits.
- Tseitin-style CNF encoding for `AND`, `OR`, `XOR`, and `NOT` gates.
- PySAT/Glucose3 CDCL solver support for scalable checks.
- Built-in DPLL solver for small examples and demonstration.
- Counterexample generation for failing equivalence checks.
- Optional ROBDD backend for learning and comparison.
- Example circuits covering ALUs, multipliers, and 64-bit adders.

## Architecture

```text
Verilog design A       Verilog design B
       |                      |
       v                      v
    Yosys                  Yosys
       |                      |
       v                      v
 Gate-level JSON        Gate-level JSON
       |                      |
       +----------+-----------+
                  v
          Internal netlists
                  |
                  v
             SAT miter
                  |
                  v
             CNF formula
                  |
                  v
           SAT solver result
```

The project uses Yosys only as the frontend. Yosys parses, elaborates, flattens, optimizes, and lowers Verilog into a normalized gate-level JSON representation. The actual equivalence logic is implemented in this repository.

Important modules:

```text
src/veqcheck/yosys_frontend.py   Runs Yosys and emits JSON
src/veqcheck/netlist.py          Loads Yosys JSON into a compact netlist model
src/veqcheck/sat_equivalence.py  Builds the miter and drives the SAT flow
src/veqcheck/cnf.py              Encodes gates as CNF clauses
src/veqcheck/sat.py              Runs Glucose3 or the in-house DPLL solver
src/veqcheck/bdd.py              Educational ROBDD implementation
src/veqcheck/cli.py              Command-line interface
```

## How The SAT Check Works

For each matching input port, the two designs are constrained to receive the same value.

For each matching output bit, the checker creates a difference signal:

```text
diff[i] = golden.out[i] XOR revised.out[i]
```

Then it asks the SAT solver whether any output difference can become true:

```text
diff[0] OR diff[1] OR ... OR diff[n] = 1
```

The result is interpreted as:

```text
SAT   -> a mismatching input exists -> NOT EQUIVALENT
UNSAT -> no mismatch is possible    -> EQUIVALENT
```

For example, if one design computes `y = a & b` and another computes `y = ~(~a | ~b)`, the output XOR can never become `1`, so the miter formula is UNSAT and the designs are equivalent.

## CNF Encoding

SAT solvers operate on CNF formulas, so each gate is translated into clauses.

For example:

```text
y = a AND b
```

is encoded as:

```text
(-a OR -b OR y)
( a OR -y)
( b OR -y)
```

Together, these clauses force `y` to be true exactly when both `a` and `b` are true. Similar encodings are implemented for `OR`, `XOR`, and `NOT`.

## Installation

Install Yosys first. On Ubuntu/Debian:

```bash
sudo apt install yosys
```

Then install the Python package:

```bash
cd verilog-equivalence-checker
python3 -m pip install -e ".[dev]"
```

The project requires Python 3.10 or newer.

## Usage

Run the checker with:

```bash
veqcheck <golden.v> <revised.v>
```

Example:

```bash
veqcheck examples/alu_v1.v examples/alu_v2.v
```

Without installing the console script, run it directly from source:

```bash
PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_v2.v
```

Expected output for an equivalent pair:

```text
EQUIVALENT
Backend: Yosys frontend + project SAT miter
SAT solver: glucose
Compared outputs: carry, out[0], out[1], out[2], out[3], parity, zero
Gates encoded: 159
CNF: 197 variables, 541 clauses
```

Expected output for a mismatch:

```text
NOT EQUIVALENT
Backend: Yosys frontend + project SAT miter
SAT solver: glucose
Output out[2] differs.
Counterexample:
  a[0] = 0
  ...
```

## Solver Selection

By default, the SAT backend uses:

```bash
--solver auto
```

In auto mode, the checker tries PySAT/Glucose3 first and falls back to the built-in DPLL solver if PySAT is unavailable.

Force Glucose3:

```bash
PYTHONPATH=src python3 -m veqcheck --solver glucose examples/adder64_ripple_v1.v examples/adder64_behavioral_v2.v
```

Force the in-house DPLL solver:

```bash
PYTHONPATH=src python3 -m veqcheck --solver dpll examples/alu_v1.v examples/alu_buggy.v
```

DPLL is useful for explanation and small examples. For larger circuits, especially equivalent 64-bit arithmetic designs, the CDCL solver is strongly preferred.

## BDD Backend

The optional BDD backend can be selected with:

```bash
PYTHONPATH=src python3 -m veqcheck --backend bdd examples/alu_v1.v examples/alu_v2.v
```

This backend uses the repository's simple Verilog parser and ROBDD implementation. It is included mainly to demonstrate canonical Boolean representation and counterexample extraction. The SAT backend is the main implementation path.

## Example Circuits

The `examples/` directory contains equivalent and intentionally buggy design pairs.

```text
examples/alu_v1.v
examples/alu_v2.v
examples/alu_buggy.v

examples/multiplier_array_v1.v
examples/multiplier_expr_v2.v
examples/multiplier_buggy.v

examples/adder64_ripple_v1.v
examples/adder64_behavioral_v2.v
examples/adder64_buggy.v
```

Covered cases:

- A 4-bit ALU with equivalent rewritten logic and an intentional operation-path bug.
- A 4x4 unsigned multiplier comparing structural and expression-based implementations.
- A 64-bit adder comparing ripple-carry and behavioral implementations.
- A 64-bit adder bug where carry propagation is broken around bit 32.

## Development

Run the test suite:

```bash
make test
```

Run the demonstration set:

```bash
make demo
```

Run a quick equivalence check:

```bash
make check
```

The automated tests exercise both the educational BDD path and the main SAT path.

## Scope And Limitations

- The main backend is intended for combinational designs.
- Input port names and widths must match between the two designs.
- Only common output ports are compared.
- The current JSON loader accepts the primitive gate types produced by the Yosys flow used here: `$_NOT_`, `$_AND_`, `$_OR_`, and `$_XOR_`.
- Sequential equivalence checking is outside the scope of this implementation.



Implementation notes:

- Yosys is used as the Verilog frontend.
- The SAT miter, CNF generation, DPLL solver, and result reporting are implemented in this project.
- PySAT/Glucose3 is used as the practical CDCL solver for larger circuits.
- The BDD backend is retained as a learning-oriented alternative.
