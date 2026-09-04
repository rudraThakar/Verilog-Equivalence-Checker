module full_adder(input a, input b, input cin, output sum, output cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule

module adder64_ripple_v1(a, b, cin, sum, cout);
  input [63:0] a, b;
  input cin;
  output [63:0] sum;
  output cout;
  wire [64:0] carry;
  genvar i;

  assign carry[0] = cin;

  generate
    for (i = 0; i < 64; i = i + 1) begin : add_bit
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
