from __future__ import annotations

from pathlib import Path

from veqcheck.equivalence import check_equivalence
from veqcheck.parser import parse_verilog


ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str):
    return parse_verilog((ROOT / "examples" / name).read_text(encoding="utf-8"))


def test_medium_large_alu_rewrite_is_equivalent():
    result = check_equivalence(load_example("alu_v1.v"), load_example("alu_v2.v"))

    assert result.equivalent
    assert {item.name for item in result.outputs} == {
        "carry",
        "out[0]",
        "out[1]",
        "out[2]",
        "out[3]",
        "parity",
        "zero",
    }
    assert result.node_count > 20


def test_medium_large_alu_bug_is_reported_with_counterexample():
    result = check_equivalence(load_example("alu_v1.v"), load_example("alu_buggy.v"))

    assert not result.equivalent
    mismatch = next(item for item in result.outputs if not item.equivalent)
    assert mismatch.name in {"out[2]", "parity", "zero"}
    assert mismatch.counterexample is not None
    assert mismatch.counterexample["sel[0]"] is True
    assert mismatch.counterexample["sel[1]"] is True


def test_medium_demorgan_factorization_equivalence():
    left = parse_verilog(
        """
        module left(a, b, c, d, y, z);
          input [3:0] a, b;
          input c, d;
          output y, z;
          wire p0, p1, p2, p3, q0, q1;
          assign p0 = (a[0] & b[0]) | (a[1] & b[1]);
          assign p1 = (a[2] & b[2]) | (a[3] & b[3]);
          assign p2 = (a[0] ^ b[1]) & (a[2] ^ b[3]);
          assign p3 = (c & p0) | (~c & p1);
          assign q0 = (d & p2) | (~d & p3);
          assign q1 = ~(~p0 & ~p1);
          assign y = q0 ^ q1;
          assign z = ~(~q0 | ~q1);
        endmodule
        """
    )
    right = parse_verilog(
        """
        module right(a, b, c, d, y, z);
          input [3:0] a, b;
          input c, d;
          output y, z;
          wire p0, p1, p2, p3, q0, q1;
          assign p0 = (a[0] & b[0]) | (a[1] & b[1]);
          assign p1 = (a[2] & b[2]) | (a[3] & b[3]);
          assign p2 = (a[0] ^ b[1]) & (a[2] ^ b[3]);
          assign p3 = (c & p0) | (~c & p1);
          assign q0 = (d & p2) | (~d & p3);
          assign q1 = p0 | p1;
          assign y = (~q0 & q1) | (q0 & ~q1);
          assign z = q0 & q1;
        endmodule
        """
    )

    result = check_equivalence(left, right)

    assert result.equivalent
    assert result.node_count > 10
