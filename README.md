# Verilog Equivalence Checker

This is a combinational equivalence checker for Verilog designs.

Yosys is used as the Verilog frontend, because writing a correct Verilog parser from scratch is not the main point of this assignment. The actual equivalence flow is implemented in this project: loading the JSON netlist, building the miter, generating CNF, running SAT, and showing counterexamples.


## What Are We Doing?

We take two versions of the same combinational circuit:

```text
golden.v   -> the original/reference design
revised.v  -> the changed/optimized design
```

Then we ask one question:

```text
Is there any input combination where the two designs give different outputs?
```

If such an input exists, the designs are **not equivalent**. If no such input exists, the designs are **equivalent**.

The flow is:

1. **Yosys reads the Verilog**

   Verilog has many syntax rules and edge cases, so we use Yosys for parsing, elaboration, flattening, and converting the circuit into a simple gate-level JSON netlist.

   Yosys gives us gates like:

   ```text
   AND, OR, XOR, NOT
   ```

   But Yosys is not doing the equivalence check for us.

2. **We load the Yosys JSON**

   Our code converts the JSON into our own internal netlist model with inputs, outputs, wires, and gates.

3. **We connect both circuits to the same inputs**

   For example, if both designs have `a[0]`, then:

   ```text
   golden.a[0] == revised.a[0]
   ```

   This means both circuits are tested under the exact same input combination.

4. **We build a miter**

   A miter is a standard equivalence-checking circuit. For every output bit, we XOR the two designs:

   ```text
   diff[0] = golden.out[0] XOR revised.out[0]
   diff[1] = golden.out[1] XOR revised.out[1]
   ```

   If any `diff` bit becomes `1`, that means at least one output is different.

5. **We convert the miter to CNF**

   SAT solvers need Boolean formulas in CNF format. So we convert every gate into CNF clauses using Tseitin encoding.

   Example idea:

   ```text
   y = a AND b
   ```

   becomes a few CNF clauses that force `y` to behave exactly like `a AND b`.

6. **We run SAT**

   Finally, we ask the SAT solver:

   ```text
   Can any output difference become 1?
   ```

   If SAT says **UNSAT**, there is no possible input where outputs differ, so the designs are equivalent.

   If SAT says **SAT**, the solver gives us a real input combination that breaks equivalence. That is printed as the counterexample.


## Features

- Uses Yosys to parse, elaborate, flatten, optimize, and emit normalized gate-level JSON.
- Implements its own internal netlist model from Yosys JSON.
- Builds a SAT miter across matching output bits.
- Encodes gates and output differences into CNF using Tseitin constraints.
- Runs PySAT/Glucose3, an open-source CDCL SAT solver, with a small built-in DPLL solver as fallback.
- Prints concrete counterexamples for non-equivalent outputs.
- Includes medium-to-large tests for ALU-style logic, a 4x4 multiplier, and a 64-bit adder.

## Quick Start

Install Yosys first if it is not already available on your machine.

```bash
cd verilog-equivalence-checker

python3 -m pip install -e ".[dev]"
python3 -m pytest
PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_v2.v
PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_buggy.v
PYTHONPATH=src python3 -m veqcheck examples/multiplier_array_v1.v examples/multiplier_expr_v2.v
PYTHONPATH=src python3 -m veqcheck examples/multiplier_array_v1.v examples/multiplier_buggy.v
PYTHONPATH=src python3 -m veqcheck examples/adder64_ripple_v1.v examples/adder64_behavioral_v2.v
PYTHONPATH=src python3 -m veqcheck examples/adder64_ripple_v1.v examples/adder64_buggy.v
```

Or use the bundled developer commands:

```bash
make test
make demo
```

After installing the project, the CLI command is also available directly:

```bash
veqcheck examples/alu_v1.v examples/alu_v2.v
```

## Choosing The SAT Solver

By default, the SAT backend uses:

```bash
--solver auto
```

In `auto` mode, the checker tries PySAT/Glucose3 first. That is the CDCL solver, and this is what we use for larger circuits like the 64-bit adder.

If we want to specifically run our own DPLL solver, use:

```bash
PYTHONPATH=src python3 -m veqcheck --solver dpll examples/alu_v1.v examples/alu_buggy.v
```

This is useful for demo/explanation because it shows that we have an in-house SAT algorithm too. But practically, run DPLL only on smaller examples like the buggy ALU or small mismatch cases. Large equivalent proofs, especially the 64-bit adder, are much better handled by Glucose/CDCL.

To force the open-source CDCL solver:

```bash
PYTHONPATH=src python3 -m veqcheck --solver glucose examples/adder64_ripple_v1.v examples/adder64_behavioral_v2.v
```

## Test Circuits

The project currently keeps three circuit families in the automated tests: one ALU, one multiplier, and one 64-bit adder. These are common enough to make sense for a digital design assignment, but they are still large enough to actually exercise the equivalence checker.

### ALU Tests

Correct pair:

```text
examples/alu_v1.v
examples/alu_v2.v
```

Both implement the same 4-bit combinational ALU behavior, but the internal logic is written differently. For example, some gates are rewritten using De Morgan style expressions, XOR is expanded in places, and the muxing structure is different. The checker should report:

```text
EQUIVALENT
```

Buggy pair:

```text
examples/alu_v1.v
examples/alu_buggy.v
```

`alu_buggy.v` has an intentional error in one alternate-operation path. The checker should report:

```text
NOT EQUIVALENT
```

It also prints the input values that expose the bug. That counterexample is important because it shows the tool is not only saying "fail"; it is giving a concrete test vector.

### Multiplier Tests

Correct pair:

```text
examples/multiplier_array_v1.v
examples/multiplier_expr_v2.v
```

Both implement the same 4x4 unsigned multiplier. The first one is written as a structural partial-product/adder network. The second one is written using shifted partial rows and `+` operators. Yosys lowers both into gates, and then our SAT miter checks whether the final `product[7:0]` bits can ever differ.

The checker should report:

```text
EQUIVALENT
```

Buggy pair:

```text
examples/multiplier_array_v1.v
examples/multiplier_buggy.v
```

`multiplier_buggy.v` has an intentional partial-product mistake. This is a realistic type of bug because one wrong bit in a multiplier array can pass many casual tests but still fail for specific input combinations.

The checker should report:

```text
NOT EQUIVALENT
```

Again, the counterexample tells exactly which `a` and `b` values make the product wrong.

### 64-Bit Adder Tests

Correct pair:

```text
examples/adder64_ripple_v1.v
examples/adder64_behavioral_v2.v
```

Both implement the same 64-bit adder with carry-in and carry-out. The first one is a structural ripple-carry adder built from a `full_adder` module and a `generate` loop. The second one is the normal behavioral Verilog style:

```text
{cout, sum} = a + b + cin
```

This is much better than a 4-bit adder test because it creates a real carry chain and also checks that the frontend can handle module instances, generate loops, and wide arithmetic.

The checker should report:

```text
EQUIVALENT
```

Buggy pair:

```text
examples/adder64_ripple_v1.v
examples/adder64_buggy.v
```

`adder64_buggy.v` intentionally breaks the carry propagation at the boundary between bit 31 and bit 32. This is a very common class of arithmetic bug: most lower bits may still look correct, but higher bits fail when a carry should cross that boundary.

The checker should report:

```text
NOT EQUIVALENT
```

The counterexample shows input values where the missing carry changes the final sum or carry-out.

## Why This Shows The Checker Works

The correct pairs are not textually identical. They are written with different internal structures, so a simple file diff or signal-name comparison would not prove anything.

The checker works because it compares behavior, not code style:

1. Same input ports are tied together.
2. Both designs are encoded into one SAT problem.
3. Output bits are XORed against each other.
4. SAT is asked whether any output difference is possible.

So:

```text
UNSAT -> no possible mismatch -> equivalent
SAT   -> mismatch exists      -> not equivalent
```

That is the main correctness idea of the project.

## Example Output

```text
EQUIVALENT
Backend: Yosys frontend + project SAT miter
Compared outputs: carry, out[0], out[1], out[2], out[3], parity, zero
Gates encoded: 159
CNF: 197 variables, 541 clauses
```

For a mismatch:

```text
NOT EQUIVALENT
Output out[2] differs.
Counterexample:
  a[0] = 0
  ...
```

## Scope

The default SAT backend supports the combinational Verilog subset that Yosys can lower to simple gates through this flow.

The optional BDD backend can be invoked with `--backend bdd`; it uses the small parser in this repository and is mainly included to demonstrate ROBDD construction.
