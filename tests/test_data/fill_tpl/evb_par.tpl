#ifdef GLU
[repulsive.start.GLU-D]

Hydronium : H3O

:::::::::::::::::::::::::::::::::::::::::::

: The parameters

H3O  : EVB_Type of H3O
OC   : Atom_Type of GLU

: ----------------------------------------------------------------------------

{voo_b:11}  : 0.125313  : B

[repulsive.end]

[repulsive.start.GLU-P]

Expon2 : Gaussian like repulsive terms V_rep = Vii + B exp[ b (R_DA - b_DA)^2 ]

GLU-P  : EVB_Type of center

: The parameters

{vii_0:11}  : constant Vii

1 : Number of pairs: 1

{vii_type_d:9}    : type D
{vii_type_a:9}    : type A
{vii_b:9}    : B
{vii_lb:9}    : b
{vii_b_da:9}    : b_DA
{vii_cut:9}    : cut-off

[repulsive.end]
#endif
