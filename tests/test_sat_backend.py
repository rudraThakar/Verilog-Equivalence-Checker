from __future__ import annotations

from pathlib import Path

from veqcheck.sat_equivalence import check_files_with_sat


ROOT = Path(__file__).resolve().parents[1]


def example(name: str) -> str:
    return str(ROOT / "examples" / name)


def test_sat_backend_proves_refactored_alu_equivalent():
    result = check_files_with_sat(example("alu_v1.v"), example("alu_v2.v"))

    assert result.equivalent
    assert result.solver == "glucose"
    assert result.gates > 100
    assert result.clauses > 400


def test_sat_backend_finds_alu_regression_counterexample():
    result = check_files_with_sat(example("alu_v1.v"), example("alu_buggy.v"))

    assert not result.equivalent
    assert result.counterexample is not None
    assert result.counterexample["sel[0]"] is True
    assert result.counterexample["sel[1]"] is True


def test_sat_backend_can_force_in_house_dpll_solver_on_small_bug():
    result = check_files_with_sat(example("alu_v1.v"), example("alu_buggy.v"), solver="dpll")

    assert not result.equivalent
    assert result.solver == "dpll"
    assert result.counterexample is not None


def test_sat_backend_handles_common_multiplier_rewrite():
    result = check_files_with_sat(example("multiplier_array_v1.v"), example("multiplier_expr_v2.v"))

    assert result.equivalent
    assert result.gates > 120
    assert result.clauses > 500


def test_sat_backend_finds_multiplier_partial_product_bug():
    result = check_files_with_sat(example("multiplier_array_v1.v"), example("multiplier_buggy.v"))

    assert not result.equivalent
    assert result.counterexample is not None
    assert result.counterexample["a[3]"] is True
    assert result.counterexample["b[2]"] != result.counterexample["b[3]"]


def test_sat_backend_handles_64_bit_adder_rewrite():
    result = check_files_with_sat(example("adder64_ripple_v1.v"), example("adder64_behavioral_v2.v"))

    assert result.equivalent
    assert result.gates > 1000
    assert result.clauses > 4000


def test_sat_backend_finds_64_bit_adder_carry_bug():
    result = check_files_with_sat(example("adder64_ripple_v1.v"), example("adder64_buggy.v"))

    assert not result.equivalent
    assert result.counterexample is not None
    assert any(output.differs and output.name == "sum[32]" for output in result.outputs)
