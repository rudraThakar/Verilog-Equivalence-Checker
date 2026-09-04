module multiplier_buggy(a, b, product);
  input [3:0] a, b;
  output [7:0] product;
  wire [7:0] row0, row1, row2, row3;
  wire [7:0] partial01, partial23;

  assign row0[0] = a[0] & b[0];
  assign row0[1] = a[1] & b[0];
  assign row0[2] = a[2] & b[0];
  assign row0[3] = a[3] & b[0];
  assign row0[4] = 1'b0;
  assign row0[5] = 1'b0;
  assign row0[6] = 1'b0;
  assign row0[7] = 1'b0;

  assign row1[0] = 1'b0;
  assign row1[1] = a[0] & b[1];
  assign row1[2] = a[1] & b[1];
  assign row1[3] = a[2] & b[1];
  assign row1[4] = a[3] & b[1];
  assign row1[5] = 1'b0;
  assign row1[6] = 1'b0;
  assign row1[7] = 1'b0;

  assign row2[0] = 1'b0;
  assign row2[1] = 1'b0;
  assign row2[2] = a[0] & b[2];
  assign row2[3] = a[1] & b[2];
  assign row2[4] = a[2] & b[2];
  assign row2[5] = a[3] & b[2];
  assign row2[6] = 1'b0;
  assign row2[7] = 1'b0;

  assign row3[0] = 1'b0;
  assign row3[1] = 1'b0;
  assign row3[2] = 1'b0;
  assign row3[3] = a[0] & b[3];
  assign row3[4] = a[1] & b[3];
  assign row3[5] = a[2] & b[3];
  assign row3[6] = a[3] & b[2];
  assign row3[7] = 1'b0;

  assign partial01 = row0 + row1;
  assign partial23 = row2 + row3;
  assign product = partial01 + partial23;
endmodule
