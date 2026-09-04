module full_adder(input a, input b, input cin, output sum, output cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule

module adder64_buggy(a, b, cin, sum, cout);
  input [63:0] a, b;
  input cin;
  output [63:0] sum;
  output cout;
  wire [64:0] carry;
  wire dropped_carry_32;
  genvar i;

  assign carry[0] = cin;

  generate
    for (i = 0; i < 31; i = i + 1) begin : add_low
      full_adder fa(
        .a(a[i]),
        .b(b[i]),
        .cin(carry[i]),
        .sum(sum[i]),
        .cout(carry[i + 1])
      );
    end
  endgenerate

  full_adder broken_boundary(
    .a(a[31]),
    .b(b[31]),
    .cin(carry[31]),
    .sum(sum[31]),
    .cout(dropped_carry_32)
  );

  assign carry[32] = carry[31];

  generate
    for (i = 32; i < 64; i = i + 1) begin : add_high
      full_adder fa(
        .a(a[i]),
        .b(b[i]),
        .cin(carry[i]),
        .sum(sum[i]),
        .cout(carry[i + 1])
      );
    end
  endgenerate

  assign cout = carry[64];
endmodule
