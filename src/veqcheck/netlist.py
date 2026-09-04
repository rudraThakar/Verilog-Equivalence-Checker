from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_CELLS = {"$_NOT_", "$_AND_", "$_OR_", "$_XOR_"}
IGNORED_CELLS = {"$scopeinfo"}


@dataclass(frozen=True)
class Gate:
    type: str
    inputs: tuple[str, ...]
    output: str


@dataclass(frozen=True)
class PortBit:
    port: str
    index: int
    bit: str

    @property
    def name(self) -> str:
        return self.port if self.index < 0 else f"{self.port}[{self.index}]"


@dataclass(frozen=True)
class Netlist:
    name: str
    inputs: dict[str, list[str]]
    outputs: dict[str, list[str]]
    gates: list[Gate]

    @property
    def input_bits(self) -> list[PortBit]:
        return _port_bits(self.inputs)

    @property
    def output_bits(self) -> list[PortBit]:
        return _port_bits(self.outputs)


class NetlistError(ValueError):
    pass


def load_yosys_json(data: dict[str, Any]) -> Netlist:
    modules = data.get("modules", {})
    if not modules:
        raise NetlistError("Yosys JSON contains no modules")

    top_name, module = _select_top(modules)
    ports = module.get("ports", {})
    inputs: dict[str, list[str]] = {}
    outputs: dict[str, list[str]] = {}

    for name, port in ports.items():
        bits = [_bit_id(bit) for bit in port["bits"]]
        if port["direction"] == "input":
            inputs[name] = bits
        elif port["direction"] == "output":
            outputs[name] = bits

    gates: list[Gate] = []
    for cell_name, cell in module.get("cells", {}).items():
        cell_type = cell["type"]
        if cell_type in IGNORED_CELLS:
            continue
        if cell_type not in SUPPORTED_CELLS:
            raise NetlistError(f"unsupported Yosys cell {cell_type} in {cell_name}")
        connections = cell["connections"]
        output = _single_bit(connections, "Y", cell_name)
        if cell_type == "$_NOT_":
            inputs_for_gate = (_single_bit(connections, "A", cell_name),)
        else:
            inputs_for_gate = (
                _single_bit(connections, "A", cell_name),
                _single_bit(connections, "B", cell_name),
            )
        gates.append(Gate(cell_type, inputs_for_gate, output))

    return Netlist(top_name, inputs, outputs, gates)


def common_output_bits(left: Netlist, right: Netlist) -> list[tuple[str, str, str]]:
    compared: list[tuple[str, str, str]] = []
    for port in sorted(set(left.outputs) & set(right.outputs)):
        if len(left.outputs[port]) != len(right.outputs[port]):
            raise NetlistError(f"output width mismatch for {port}")
        for index, (left_bit, right_bit) in enumerate(zip(left.outputs[port], right.outputs[port])):
            name = port if len(left.outputs[port]) == 1 else f"{port}[{index}]"
            compared.append((name, left_bit, right_bit))
    if not compared:
        raise NetlistError("designs have no common output bits")
    return compared


def validate_compatible_inputs(left: Netlist, right: Netlist) -> None:
    if set(left.inputs) != set(right.inputs):
        raise NetlistError("input ports do not match")
    for port in sorted(left.inputs):
        if len(left.inputs[port]) != len(right.inputs[port]):
            raise NetlistError(f"input width mismatch for {port}")


def _select_top(modules: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for name, module in modules.items():
        if module.get("attributes", {}).get("top") == "00000000000000000000000000000001":
            return name, module
    if len(modules) == 1:
        return next(iter(modules.items()))
    raise NetlistError("could not determine top module")


def _single_bit(connections: dict[str, list[Any]], port: str, cell_name: str) -> str:
    bits = connections.get(port)
    if not bits or len(bits) != 1:
        raise NetlistError(f"cell {cell_name} port {port} is not one bit")
    return _bit_id(bits[0])


def _bit_id(bit: Any) -> str:
    if bit in (0, "0"):
        return "0"
    if bit in (1, "1"):
        return "1"
    return f"n{bit}"


def _port_bits(ports: dict[str, list[str]]) -> list[PortBit]:
    result: list[PortBit] = []
    for port in sorted(ports):
        bits = ports[port]
        for index, bit in enumerate(bits):
            result.append(PortBit(port, -1 if len(bits) == 1 else index, bit))
    return result
