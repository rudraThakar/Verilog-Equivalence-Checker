module alu_v1(a, b, sel, out, carry, parity, zero);
  input [3:0] a, b;
  input [1:0] sel;
  output [3:0] out;
  output carry, parity, zero;
  wire [3:0] and_r, xor_r, sum, mux0, mux1;
  wire c1, c2, c3;

  assign and_r[0] = a[0] & b[0];
  assign and_r[1] = a[1] & b[1];
  assign and_r[2] = a[2] & b[2];
  assign and_r[3] = a[3] & b[3];

  assign xor_r[0] = a[0] ^ b[0];
  assign xor_r[1] = a[1] ^ b[1];
  assign xor_r[2] = a[2] ^ b[2];
  assign xor_r[3] = a[3] ^ b[3];

  assign sum[0] = a[0] ^ b[0];
  assign c1 = a[0] & b[0];
  assign sum[1] = a[1] ^ b[1] ^ c1;
  assign c2 = (a[1] & b[1]) | (a[1] & c1) | (b[1] & c1);
  assign sum[2] = a[2] ^ b[2] ^ c2;
  assign c3 = (a[2] & b[2]) | (a[2] & c2) | (b[2] & c2);
  assign sum[3] = a[3] ^ b[3] ^ c3;
  assign carry = (a[3] & b[3]) | (a[3] & c3) | (b[3] & c3);

  assign mux0[0] = (sel[0] & xor_r[0]) | (~sel[0] & and_r[0]);
  assign mux0[1] = (sel[0] & xor_r[1]) | (~sel[0] & and_r[1]);
  assign mux0[2] = (sel[0] & xor_r[2]) | (~sel[0] & and_r[2]);
  assign mux0[3] = (sel[0] & xor_r[3]) | (~sel[0] & and_r[3]);

  assign mux1[0] = (sel[0] & ~a[0]) | (~sel[0] & sum[0]);
  assign mux1[1] = (sel[0] & ~a[1]) | (~sel[0] & sum[1]);
  assign mux1[2] = (sel[0] & ~a[2]) | (~sel[0] & sum[2]);
  assign mux1[3] = (sel[0] & ~a[3]) | (~sel[0] & sum[3]);

  assign out[0] = (sel[1] & mux1[0]) | (~sel[1] & mux0[0]);
  assign out[1] = (sel[1] & mux1[1]) | (~sel[1] & mux0[1]);
  assign out[2] = (sel[1] & mux1[2]) | (~sel[1] & mux0[2]);
  assign out[3] = (sel[1] & mux1[3]) | (~sel[1] & mux0[3]);
  assign parity = out[0] ^ out[1] ^ out[2] ^ out[3];
  assign zero = ~out[0] & ~out[1] & ~out[2] & ~out[3];
endmodule
