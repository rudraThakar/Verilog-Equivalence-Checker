module multiplier_array_v1(a, b, product);
  input [3:0] a, b;
  output [7:0] product;
  wire pp00, pp01, pp02, pp03;
  wire pp10, pp11, pp12, pp13;
  wire pp20, pp21, pp22, pp23;
  wire pp30, pp31, pp32, pp33;
  wire s11, c11, s12, c12, s13, c13;
  wire s21, c21, s22, c22, s23, c23;
  wire s31, c31, s32, c32, s33, c33;
  wire s41, c41, s42, c42;

  assign pp00 = a[0] & b[0];
  assign pp01 = a[0] & b[1];
  assign pp02 = a[0] & b[2];
  assign pp03 = a[0] & b[3];
  assign pp10 = a[1] & b[0];
  assign pp11 = a[1] & b[1];
  assign pp12 = a[1] & b[2];
  assign pp13 = a[1] & b[3];
  assign pp20 = a[2] & b[0];
  assign pp21 = a[2] & b[1];
  assign pp22 = a[2] & b[2];
  assign pp23 = a[2] & b[3];
  assign pp30 = a[3] & b[0];
  assign pp31 = a[3] & b[1];
  assign pp32 = a[3] & b[2];
  assign pp33 = a[3] & b[3];

  assign product[0] = pp00;
  assign product[1] = pp01 ^ pp10;
  assign c11 = pp01 & pp10;

  assign s12 = pp02 ^ pp11 ^ pp20;
  assign c12 = (pp02 & pp11) | (pp02 & pp20) | (pp11 & pp20);
  assign product[2] = s12 ^ c11;
  assign c21 = s12 & c11;

  assign s13 = pp03 ^ pp12 ^ pp21;
  assign c13 = (pp03 & pp12) | (pp03 & pp21) | (pp12 & pp21);
  assign s22 = s13 ^ pp30 ^ c12;
  assign c22 = (s13 & pp30) | (s13 & c12) | (pp30 & c12);
  assign product[3] = s22 ^ c21;
  assign c31 = s22 & c21;

  assign s23 = pp13 ^ pp22 ^ pp31;
  assign c23 = (pp13 & pp22) | (pp13 & pp31) | (pp22 & pp31);
  assign s32 = s23 ^ c13 ^ c22;
  assign c32 = (s23 & c13) | (s23 & c22) | (c13 & c22);
  assign product[4] = s32 ^ c31;
  assign c41 = s32 & c31;

  assign s33 = pp23 ^ pp32 ^ c23;
  assign c33 = (pp23 & pp32) | (pp23 & c23) | (pp32 & c23);
  assign s42 = s33 ^ c32 ^ c41;
  assign c42 = (s33 & c32) | (s33 & c41) | (c32 & c41);
  assign product[5] = s42;
  assign product[6] = pp33 ^ c33 ^ c42;
  assign product[7] = (pp33 & c33) | (pp33 & c42) | (c33 & c42);
endmodule
