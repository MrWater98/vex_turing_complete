module ripple4_add (
    input  wire a0,
    input  wire a1,
    input  wire a2,
    input  wire a3,
    input  wire b0,
    input  wire b1,
    input  wire b2,
    input  wire b3,
    input  wire cin,
    output wire s0,
    output wire s1,
    output wire s2,
    output wire s3,
    output wire cout
);
    wire p0, p1, p2, p3;
    wire c1, c2, c3;

    assign p0 = a0 ^ b0;
    assign p1 = a1 ^ b1;
    assign p2 = a2 ^ b2;
    assign p3 = a3 ^ b3;

    assign s0 = p0 ^ cin;
    assign c1 = (a0 & b0) | (p0 & cin);
    assign s1 = p1 ^ c1;
    assign c2 = (a1 & b1) | (p1 & c1);
    assign s2 = p2 ^ c2;
    assign c3 = (a2 & b2) | (p2 & c2);
    assign s3 = p3 ^ c3;
    assign cout = (a3 & b3) | (p3 & c3);
endmodule
