.PHONY: test check demo

test:
	python3 -m pytest

check: test
	env PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_v2.v

demo:
	env PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_v2.v
	env PYTHONPATH=src python3 -m veqcheck examples/alu_v1.v examples/alu_buggy.v || true
	env PYTHONPATH=src python3 -m veqcheck examples/multiplier_array_v1.v examples/multiplier_expr_v2.v
	env PYTHONPATH=src python3 -m veqcheck examples/multiplier_array_v1.v examples/multiplier_buggy.v || true
	env PYTHONPATH=src python3 -m veqcheck examples/adder64_ripple_v1.v examples/adder64_behavioral_v2.v
	env PYTHONPATH=src python3 -m veqcheck examples/adder64_ripple_v1.v examples/adder64_buggy.v || true

benchmark:
	env PYTHONPATH=src python3 -m veqcheck examples/adder64_ripple_v1.v examples/adder64_buggy.v || true
