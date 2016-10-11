::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::                                                                          ::
::  FILE: PARAMETER FILE FOR LAMMPS_EVB                                     ::
::  DATE: 2016-06-20 UPDATED FOR EVB3.2 by H.MAYES                          ::
::        2016-07-19 UPDATED FOR ALT GLU COUPLING BY H. MAYES               ::
::  COMM: (1) WATER EVB2 & EVB3.2                                           ::
::        (2) ASP & GLU (glu params verified; asp need revision)            ::
::                                                                          ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
:::S                                                                      S:::
:::S   SEGMENT:   MOLECULE TYPE (EVB KERNEL TYPE)                         S:::
:::S                                                                      S:::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
[segment.molecule_type]
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef WAT

[molecule_type.start.H3O]

:      HO        2
:      |         |
:      OH        1
:     / \       / \
:   HO   HO    3   4

: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
              4        3        3         0           0          1
: atomic information
: atom type   charge   kernel
  OH          -0.32     1
  HO           0.44     1
  HO           0.44     1
  HO           0.44     1
: bonds
:  atom 1       atom 2      type
   1            2           OH-HO
   1            3           OH-HO
   1            4           OH-HO
: angles
:  atom 1       atom 2       atom 3     type
   2            1            3          HO-OH-HO
   2            1            4          HO-OH-HO
   3            1            4          HO-OH-HO

: COC
4
1 2 3 4

[molecule_type.end]

: ----------------------------------------------------------------------------

[molecule_type.start.H2O]

: HW---OW---HW      2---1---3

: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
              3        2        1         0           0          0
: atomic information

: atom type   charge   kernel

  #ifdef EVB3

  OW          -0.82     1
  HW           0.41     1
  HW           0.41     1

  #endif

  #ifdef EVB2

  OW          -0.834    1
  HW           0.417    1
  HW           0.417    1

  #endif

: bonds
:  atom 1       atom 2      type
   1            2           OW-HW
   1            3           OW-HW
: angles
:  atom 1       atom 2       atom 3     type
   2            1            3          HW-OW-HW

[molecule_type.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef ASP

[molecule_type.start.ASP-P]

:     |                                              |
:  H--NH1                                         H--NH1
:     |     HA     OB              2     5           |     HA2    OB
:     |     |     //               |    //           |     |     //
: HB--CT1---CT2--CD         ---8---1---4         HB--CT2A--CT2--CD
:     |     |     \                |    \            |     |     \
:     |     HA     OH1--H          3     6--7        |     HA2    OH1--H
:   O=C                                            O=C
:     |                                              |
:
:              |<-kernel->|
: |<-env->|<-----evb----->|


: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
             8          4          4          8          1          1

: atomic information
: atom type   charge  evb_bond
      CT2     -0.210         0   : 1
      HA       0.090         0   : 2
      HA       0.090         0   : 3
      CD       0.750         1   : 4
      OB      -0.550         1   : 5
      OH1     -0.610         1   : 6
      H        0.440         1   : 7
      CT1      0.070         0   : 8

: bonds
:  atom_I   atom_J   type_ID
      4        1     ASPP_BOND_1  :  CD   CT2
      4        5     ASPP_BOND_2  :  CD   OB
      6        4     ASPP_BOND_3  :  CD   OH1
      6        7     ASPP_BOND_4  :  H    OH1

: angles
:  atom_I   atom_J   atom_K   type_ID
      1        4        5     ASPP_ANGLE_1
      1        4        6     ASPP_ANGLE_2
      5        4        6     ASPP_ANGLE_3
      4        6        7     ASPP_ANGLE_4

: dihedrals
:  atom_I   atom_J   atom_K   atom_L   type_ID
      5        4        1        2     ASPP_DIHEDRAL_1
      5        4        1        3     ASPP_DIHEDRAL_1
      5        4        1        8     ASPP_DIHEDRAL_1
      6        4        1        2     ASPP_DIHEDRAL_1
      6        4        1        3     ASPP_DIHEDRAL_1
      6        4        1        8     ASPP_DIHEDRAL_1
      1        4        6        7     ASPP_DIHEDRAL_2
      5        4        6        7     ASPP_DIHEDRAL_2

: impropers
:  atom_I   atom_J   atom_K   atom_L   type_ID
      5        6        1        4     ASPP_IMPROPER_1

: COC information
2 : number of COC atoms
6  7 : index of COC atoms

[molecule_type.end]

: ----------------------------------------------------------------------------

[molecule_type.start.ASP-D]

:     |
:  H--NH1
:     |     HA     OC              2     5
:     |     |     //               |    //
: HB--CT1---CT2--CC         ---7---1---4
:     |     |     \                |    \
:     |     HA     OC(-)           3     6
:   O=C
:     |
:
:              |<-kernel->|
: |<-env->|<-----evb----->|

: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
             7          3          3          6          1          0

: atomic information
: atom type   charge  evb_bond
      CT2     -0.280         0   : 1
      HA       0.090         0   : 2
      HA       0.090         0   : 3
      CC       0.620         1   : 4
      OC      -0.760         1   : 5
      OC      -0.760         1   : 6
      CT1      0.070         0   : 7

: bonds
:  atom_I   atom_J   type_ID
      4        1     ASP_BOND_1
      4        5     ASP_BOND_2
      4        6     ASP_BOND_2

: angles
:  atom_I   atom_J   atom_K   type_ID
      1        4        5     ASP_ANGLE_1
      1        4        6     ASP_ANGLE_1
      5        4        6     ASP_ANGLE_2

: dihedrals
:  atom_I   atom_J   atom_K   atom_L   type_ID
      5        4        1        2     ASP_DIHEDRAL_1
      5        4        1        3     ASP_DIHEDRAL_1
      5        4        1        7     ASP_DIHEDRAL_1
      6        4        1        2     ASP_DIHEDRAL_1
      6        4        1        3     ASP_DIHEDRAL_1
      6        4        1        7     ASP_DIHEDRAL_1

: impropers
:  atom_I   atom_J   atom_K   atom_L   type_ID
      5        6        1        4     ASP_IMPROPER_1

[molecule_type.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef GLU

[molecule_type.start.GLU-P]

:     |
:  H--NH1
:     |     HA2  HA2    OB              2     5
:     |     |    |     //               |    //
: HB--CT1--CT2A--CT2--CD        9---8---1---4
:     |     |    |     \                |    \
:     |     HA2  HA2    OH1--H          3     6--7
:   O=C
:     |
:
:              |<-kernel->|
: |<-env->|<-----evb----->|


: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
             9          4         10          9          1          1

: atomic information
: atom type   charge  evb_bond
      CT2     -0.210         1   : 1  22    (11)
      HA       0.090         0   : 2     23 (7)
      HA       0.090         0   : 3     24
      CD       0.750         1   : 4  25    (20)
      OB      -0.550         1   : 5  26    (18)
      OH1     -0.610         1   : 6  27    (19)
      H        0.440         1   : 7  31    (5)
      CT2A    -0.180         0   : 8     19 (12)
      CT1      0.070         0   : 9     17 (10)

: bonds
:  atom_I   atom_J   type_ID
      4        1     GLUP_BOND_CD_CT2  :  CD_CT2 GLUP_BOND_1
      4        5     GLUP_BOND_CD_OB   :  CD_OB  GLUP_BOND_2
      4        6     GLUP_BOND_CD_OH1  :  CD_OH1 GLUP_BOND_3
      6        7     GLUP_BOND_OH1_H   :  OH1_H  GLUP_BOND_4

: angles
:  atom_I   atom_J   atom_K   type_ID
      1        4        5     GLUP_ANG_CT2_CD_OB   : GLUP_ANGLE_1
      1        4        6     GLUP_ANG_CT2_CD_OH1  : GLUP_ANGLE_2
      5        4        6     GLUP_ANG_OB_CD_OH1   : GLUP_ANGLE_3
      4        6        7     GLUP_ANG_CD_OH1_H    : GLUP_ANGLE_4
      7        1        2     GLU_ANG_CT2A_CT2_HA2 : 19 (needed to add due to ownership)
      7        1        3     GLU_ANG_CT2A_CT2_HA2 : 19 (needed to add due to ownership)
      7        1        4     GLU_ANG_C_CT2_HA2    :  8 (needed to add due to ownership) CC CT2 CT2A (same as CD CT2 CT2A)
      2        1        3     GLU_ANG_HA2_CT2_HA2  : 23 (needed to add due to ownership)
      4        1        2     GLU_ANG_C_CT2_HA2    :  9 (needed to add due to ownership) (same as CD CT2 HA2)
      4        1        3     GLU_ANG_C_CT2_HA2    :  9 (needed to add due to ownership) (same as CD CT2 HA2)


: dihedrals
:  atom_I   atom_J   atom_K   atom_L   type_ID                 : Previous name
      2        1        4        5   GLUP_DIHE_HA2_CT2_CD_OB   : GLUP_DIHEDRAL_1
      3        1        4        5   GLUP_DIHE_HA2_CT2_CD_OB   :
      2        1        4        6   GLUP_DIHE_HA2_CT2_CD_OH1  : GLUP_DIHEDRAL_2
      3        1        4        6   GLUP_DIHE_HA2_CT2_CD_OH1  :
      4        1        8        9   GLUP_DIHE_CD_CT2_CT2A_CT1 : GLUP_DIHEDRAL_3
      1        4        6        7   GLUP_DIHE_CT2_CD_OH1_H    :
      5        4        1        8   GLUP_DIHE_CT2A_CT2_CD_OB  : GLUP_DIHEDRAL_4
      5        4        6        7   GLUP_DIHE_H_OH1_CD_OB     :
      6        4        1        8   GLUP_DIHE_CT2A_CT2_CD_OH1 : GLUP_DIHEDRAL_5

: impropers
:  atom_I   atom_J   atom_K   atom_L   type_ID
      4        1        6        5    GLUP_IMPR_CD_CT2_OH1_OB   : GLUP_IMPROPER_1

: COC information
2 : number of COC atoms
6  7 : index of COC atoms

[molecule_type.end]

: ----------------------------------------------------------------------------

[molecule_type.start.GLU-D]

:     |
:  H--NH1
:     |     HA2  HA2    OC              2     5
:     |     |    |     //               |    //
: HB--CT1--CT2A--CT2--CC        8---7---1---4
:     |     |    |     \                |    \
:     |     HA2  HA2    OC(-)           3     6
:   O=C
:     |
:              |<-kernel->|
: |<-env->|<-----evb----->|

: number of atoms,   bonds,   angles,  dihedrals,   impropers,   starting rc
             8          3          9          9          1          0

: atomic information
: atom type   charge  evb_bond
      CT2     -0.280         1   : 1  22    (11)
      HA       0.090         0   : 2     23 (7)
      HA       0.090         0   : 3     24
      CC       0.620         1   : 4  25    (14)
      OC      -0.760         1   : 5  26    (17)
      OC      -0.760         1   : 6  27
      CT2A    -0.180         0   : 7     19 (12)
      CT1      0.070         0   : 8     17 (10)

: bonds
:  atom_I   atom_J   type_ID
      4        1     GLUE_BOND_CC_CT2  : CC   CT2 (5)
      4        5     GLUE_BOND_CC_OC   : CC   OC  (6)
      4        6     GLUE_BOND_CC_OC   : CC   OC  (6)

: angles
:  atom_I   atom_J   atom_K   type_ID
      1        4        5     GLUE_ANG_CT2_CC_OC    : 15
      1        4        6     GLUE_ANG_CT2_CC_OC    : 15
      5        4        6     GLUE_ANG_OC_CC_OC     : 31
      7        1        2     GLU_ANG_CT2A_CT2_HA2  : 19 (needed to add due to ownership)
      7        1        3     GLU_ANG_CT2A_CT2_HA2  : 19 (needed to add due to ownership)
      7        1        4     GLU_ANG_C_CT2_HA2     :  8 (needed to add due to ownership) CC CT2 CT2A (same as CD CT2 CT2A)
      2        1        3     GLU_ANG_HA2_CT2_HA2   : 23 (needed to add due to ownership)
      4        1        2     GLU_ANG_C_CT2_HA2     :  9 (needed to add due to ownership) (same as CD CT2 HA2)
      4        1        3     GLU_ANG_C_CT2_HA2     :  9 (needed to add due to ownership) (same as CD CT2 HA2)

: dihedrals
:  atom_I   atom_J   atom_K   atom_L   type_ID
      4        1        7        8   GLUE_DIHEDRAL_1  : CC   CT2 CT2A CT1 GLUE_DIHE_CC_CT2_CT2A_CT1_1
      4        1        7        8   GLUE_DIHEDRAL_2  : CC   CT2 CT2A CT1 GLUE_DIHE_CC_CT2_CT2A_CT1_2
      4        1        7        8   GLUE_DIHEDRAL_3  : CC   CT2 CT2A CT1 GLUE_DIHE_CC_CT2_CT2A_CT1_3
      7        1        4        5   GLUE_DIHE_CT2A_CT2_CC_OC : CT2A CT2 CC   OC
      7        1        4        6   GLUE_DIHE_CT2A_CT2_CC_OC : CT2A CT2 CC   OC
      2        1        4        5   GLUE_DIHE_HA2_CT2_CC_OC  :  HA2  CT2 CC   OC
      2        1        4        6   GLUE_DIHE_HA2_CT2_CC_OC  :  HA2  CT2 CC   OC
      3        1        4        5   GLUE_DIHE_HA2_CT2_CC_OC  :  HA2  CT2 CC   OC
      3        1        4        6   GLUE_DIHE_HA2_CT2_CC_OC  :  HA2  CT2 CC   OC

: impropers
:  atom_I   atom_J   atom_K   atom_L   type_ID
      4        1        5         6  GLUE_IMPR_CC_CT2_OC_OC : CC   CT2  OC   OC

[molecule_type.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

[segment.end]

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
:::S                                                                      S:::
:::S   SEGMENT:   REACTION (REACTIONS TYPE AND PATHS)                     S:::
:::S                                                                      S:::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
[segment.reaction]
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef WAT_WAT

[reaction.start.H3O_H2O]

: For reaction pair 1 :  hydronium + water -> water + hydronium
0            : is the atom moving from molecule B to molecule A,  0-forward,  1-backward
H3O   H2O    : change of molecule A (Hydronium->Water)
H2O   H3O    : change of molecule B (Water->Hydronium)
3            : number of possible pathways

: ----------------------------------------------------------------------------

: Pathway 1
: A description of reaction contains three parts:
1    3    3 : number of moving part, first part, second part
: moving part:
2    2      : the index 2 atom of type 1 will turn into index 2 atom of type 2 (HO from Hydronium to Water)
: rest part: ( first type in the pair )
1    1      : index 1 atom in reactant will become index 1 atom in product (OH->OW)
3    2      : index 3 atom in reactant will become index 2 atom in product (HO->HW)
4    3      : index 4 atom in reactant will become index 3 atom in product (OH->OW)
: newing part: ( second type in the pair )
1    1      : index 1 atom in reactant will become index 1 atom in product (OW->OH)
2    3      : index 2 atom in reactant will become index 3 atom in product (HW->HO)
3    4      : index 3 atom in reactant will become index 4 atom in product (HW->HO)

: ----------------------------------------------------------------------------

: Pathway 2
: A description of reaction contains three parts:
1    3    3   : number of moving part, first part, second part
: moving part:
3    2           : the index 3 atom of type 1 will turn into index 2 atom of type 2 (HO from Hydronium to Water)
: rest part: ( first type in the pair )
1    1     : index 1 atom in reactant will become index 1 atom in product (OH->OW)
2    2     : index 2 atom in reactant will become index 2 atom in product (HO->HW)
4    3     : index 4 atom in reactant will become index 3 atom in product (OH->OW)
: newing part: ( second type in the pair )
1    1     : index 1 atom in reactant will become index 1 atom in product (OW->OH)
2    3     : index 2 atom in reactant will become index 3 atom in product (HW->HO)
3    4     : index 3 atom in reactant will become index 4 atom in product (HW->HO)

: ----------------------------------------------------------------------------

: Pathway 3
: A description of reaction contains three parts:
1    3    3   : number of moving part, first part, second part
: moving part:
4    2           : the index 4 atom of type 1 will turn into index 2 atom of type 2 (HO from Hydronium to Water)
: rest part: ( first type in the pair )
1    1     : index 1 atom in reactant will become index 1 atom in product (OH->OW)
2    2     : index 2 atom in reactant will become index 2 atom in product (HO->HW)
3    3     : index 4 atom in reactant will become index 3 atom in product (OH->OW)
: newing part: ( second type in the pair )
1    1     : index 1 atom in reactant will become index 1 atom in product (OW->OH)
2    3     : index 2 atom in reactant will become index 3 atom in product (HW->HO)
3    4     : index 3 atom in reactant will become index 4 atom in product (HW->HO)

[reaction.end]

: ----------------------------------------------------------------------------

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef ASP_WAT

: ----------------------------------------------------------------------------

[reaction.start.H3O_ASP-D]

0              : 0-forward,  1-backward
H3O     H2O    : change of molecule A (Hydronium->Water)
ASP-D   ASP-P  : change of molecule B (HIE->HIP)
6              : number of possible pathways

: Pathway 1-3: HW->OC(5); Pathway 4-6: HW->OC(6)
: Pathway 1,4: HW(2)->OC; Pathway 2,5: HW(3)->OC; Pathway 1,4: HW(4)->OC;

: ----------------------------------------------------------------------------

: Pathway 1
: A description of reaction contains three parts:
1    3    7   : number of moving part, first part, second part
: moving part:
2    7     :
: rest part: ( first type in the pair )
1    1     :
3    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 2
: A description of reaction contains three parts:
1    3    7   : number of moving part, first part, second part
: moving part:
3    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8

: ----------------------------------------------------------------------------

: Pathway 3
: A description of reaction contains three parts:
1    3    7   : number of moving part, first part, second part
: moving part:
4    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8

: ----------------------------------------------------------------------------

: Pathway 4
: A description of reaction contains three parts:
1    3     7   : number of moving part, first part, second part
: moving part:
2    7     :
: rest part: ( first type in the pair )
1    1     :
3    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8

: ----------------------------------------------------------------------------

: Pathway 5
: A description of reaction contains three parts:
1    3     7   : number of moving part, first part, second part
: moving part:
3    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8

: ----------------------------------------------------------------------------

: Pathway 6
: A description of reaction contains three parts:
1    3     7   : number of moving part, first part, second part
: moving part:
4    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8

[reaction.end]

: ----------------------------------------------------------------------------

[reaction.start.ASP-P_H2O]

0                : 0-forward,  1-backward
ASP-P   ASP-D    : change of molecule A (Hydronium->Water)
H2O     H3O      : change of molecule B (Water->Hydronium)
1                : number of possible pathways

: Pathway 1
: A description of reaction contains three parts:
1    7    3    : number of moving part, first part, second part
: moving part:
7    2         : the index 3 atom of type 1 will turn into index 2 atom of type 2 (HO from Hydronium to HIE)
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
8    7

: newing part: ( second type in the pair )
1    1
2    3
3    4

[reaction.end]

: ----------------------------------------------------------------------------

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef GLU_WAT

: ----------------------------------------------------------------------------

[reaction.start.H3O_GLU-D]

0              : 0-forward,  1-backward
H3O     H2O    : change of molecule A (Hydronium->Water)
GLU-D   GLU-P  : change of molecule B (HIE->HIP)
6              : number of possible pathways

: Pathway 1-3: HW->OC(5); Pathway 4-6: HW->OC(6)
: Pathway 1,4: HW(2)->OC; Pathway 2,5: HW(3)->OC; Pathway 1,4: HW(4)->OC;

: ----------------------------------------------------------------------------

: Pathway 1
: A description of reaction contains three parts:
1    3    8   : number of moving part, first part, second part
: moving part:
2    7     :
: rest part: ( first type in the pair )
1    1     :
3    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 2
: A description of reaction contains three parts:
1    3    8   : number of moving part, first part, second part
: moving part:
3    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 3
: A description of reaction contains three parts:
1    3    8   : number of moving part, first part, second part
: moving part:
4    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    6
6    5
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 4
: A description of reaction contains three parts:
1    3     8   : number of moving part, first part, second part
: moving part:
2    7     :
: rest part: ( first type in the pair )
1    1     :
3    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 5
: A description of reaction contains three parts:
1    3     8   : number of moving part, first part, second part
: moving part:
3    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
4    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8
8    9

: ----------------------------------------------------------------------------

: Pathway 6
: A description of reaction contains three parts:
1    3     8   : number of moving part, first part, second part
: moving part:
4    7     :
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
: newing part: ( second type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
7    8
8    9

[reaction.end]

: ----------------------------------------------------------------------------

[reaction.start.GLU-P_H2O]

0                : 0-forward,  1-backward
GLU-P   GLU-D    : change of molecule A (Hydronium->Water)
H2O     H3O      : change of molecule B (Water->Hydronium)
1                : number of possible pathways

: Pathway 1
: A description of reaction contains three parts:
1    8    3    : number of moving part, first part, second part
: moving part:
7    2         : the index 3 atom of type 1 will turn into index 2 atom of type 2 (HO from Hydronium to HIE)
: rest part: ( first type in the pair )
1    1     :
2    2     :
3    3     :
4    4
5    5
6    6
8    7
9    8

: newing part: ( second type in the pair )
1    1
2    3
3    4

[reaction.end]

: ----------------------------------------------------------------------------

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

[segment.end]


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
:::S                                                                      S:::
:::S   SEGMENT:   STATE SEARCH ALGORITHMN                                 S:::
:::S                                                                      S:::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
[segment.state_search]
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::is refining states
#ifdef EVB3
  0
#endif

#ifdef EVB2
  1
#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef WAT

[state_search.start.H3O]

  #ifdef WAT_WAT
  : host;  target;  client;   shell limit;   distance limit;    reaction pair;  reaction path
  : H->OW
    2      H2O         1            3                2.5        H3O_H2O           1
    3      H2O         1            3                2.5        H3O_H2O           2
    4      H2O         1            3                2.5        H3O_H2O           3
  #endif

: ----------------------------------------------------------------------------

  #ifdef ASP_WAT
  : H->OC
    2      ASP-D       5            3                3.50       H3O_ASP-D         1
    3      ASP-D       5            3                3.50       H3O_ASP-D         2
    4      ASP-D       5            3                3.50       H3O_ASP-D         3
    2      ASP-D       6            3                3.50       H3O_ASP-D         4
    3      ASP-D       6            3                3.50       H3O_ASP-D         5
    4      ASP-D       6            3                3.50       H3O_ASP-D         6
  #endif

: ----------------------------------------------------------------------------

  #ifdef GLU_WAT
  : H->OC
    2      GLU-D       5            3                3.50       H3O_GLU-D         1
    3      GLU-D       5            3                3.50       H3O_GLU-D         2
    4      GLU-D       5            3                3.50       H3O_GLU-D         3
    2      GLU-D       6            3                3.50       H3O_GLU-D         4
    3      GLU-D       6            3                3.50       H3O_GLU-D         5
    4      GLU-D       6            3                3.50       H3O_GLU-D         6
  #endif

[state_search.end]

: ----------------------------------------------------------------------------

[state_search.start.H2O]

  #ifdef WAT_WAT
  : host;  target;  client;   shell limit;   distance limit;    reaction pair;  reaction path
  : H->OW
    2      H2O         1            3                2.5        H3O_H2O           2
    3      H2O         1            3                2.5        H3O_H2O           3
  #endif

: ----------------------------------------------------------------------------

  #ifdef ASP_WAT
  : H->OC
    2      ASP-D       5            3                3.50       H3O_ASP-D         2
    3      ASP-D       5            3                3.50       H3O_ASP-D         3
    2      ASP-D       6            3                3.50       H3O_ASP-D         5
    3      ASP-D       6            3                3.50       H3O_ASP-D         6
  #endif

: ----------------------------------------------------------------------------

  #ifdef GLU_WAT
  : H->OC
    2      GLU-D       5            3                3.50       H3O_GLU-D         2
    3      GLU-D       5            3                3.50       H3O_GLU-D         3
    2      GLU-D       6            3                3.50       H3O_GLU-D         5
    3      GLU-D       6            3                3.50       H3O_GLU-D         6
  #endif

[state_search.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef ASP

[state_search.start.ASP-P]

  #ifdef ASP_WAT
     7     H2O         1            3                3.50       ASP-P_H2O         1
  #endif

[state_search.end]

: ----------------------------------------------------------------------------

[state_search.start.ASP-D]
[state_search.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef GLU

[state_search.start.GLU-P]

  #ifdef GLU_WAT
     7     H2O         1            3                3.50       GLU-P_H2O         1
  #endif

[state_search.end]

: ----------------------------------------------------------------------------

[state_search.start.GLU-D]
[state_search.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

[segment.end]

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
:::S                                                                      S:::
:::S   SEGMENT:   OFF_DIAGONAL COUPLINGS                                  S:::
:::S                                                                      S:::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
[segment.off_diagonal]
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

::::::::::::::::::::::::::::::::::::::
: for pt of H3O->H2O
::::::::::::::::::::::::::::::::::::::

#ifdef WAT_WAT

[off_diagonal.start.H3O_H2O]

PT  : Use the PT coupling

: Geometry part

 : Geometry part

  : atom index
 1  1              : evb_index of DONOR atom (should be in molecule A)
 2  1              : evb_index of ACCEPT atom (should be in molecule B)
 2  2              : evb_index of HYDROGEN atom (should be in molecule B)

  : A_Rq Type : A(R,q) = f(R) * g(q)
 1 : 1-symmetric; 2-asymmetric

: ----------------------------------------------------------------------------

  #ifdef EVB3

  : parameters
   1.783170     : g
   0.155905     : P
   5.066447     : k
   2.862169     : D_oo
   5.239413     : b
   2.942597     : R0_oo
   7.614767     : P'
   7.406262     : a
   1.800000     : r0_oo

 : Potential part
   -21.064268   : vij_const, in kcal/mol
     1          : if contains Vij_ex part

  : exchanged charge
   H2O  H3O : Types of molecule_A (Water) and molecule_B (Hydronium)

   -0.0895456
    0.0252683
    0.0252683
   -0.0895456
    0.0780180
    0.0252683
    0.0252683

  #endif

: ----------------------------------------------------------------------------

  #ifdef EVB2

  : parameters
:
   1.85           : gamma
   0.27           : P
   11.5           : k
   2.875          : D_oo
   4.50           : beta
   3.14           : R0_oo
   10.0           : P'
   12.0           : alpha
   1.88           : r0_oo

 : Potential part
   -32.419        : vij_const, in kcal/mol
     1                : if contains Vij_ex part

  : exchanged charge
   H2O  H3O : Types of molecule_A (Water) and molecule_B (Hydronium)

   -0.116725
    0.04669
    0.04669
   -0.116725
    0.04669
    0.04669
    0.04669

  #endif

[off_diagonal.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef GLU_WAT

[off_diagonal.start.GLU-P_H2O]

  PT : Type of coupling: Proton Transfer
  1 6  : evb_index of DONOR atom (should be in molecule A)
  2 1  : evb_index of ACCEPT atom (should be in molecule B)
  2 2  : evb_index of HYDROGEN atom (should be in molecule B)

   : A_Rq Type : A(R,q) = f(R) * g(q)
  2 : 1-symmetric; 2-asymmetric

  : parameters
     @@@r0_sc  : r0_sc
     @@@lambda : lambda
     0.00      : R0_DA  not required
     1.00      : C
     @@@arq_alp  : alpha
     @@@a_da     : a_DA
     0.00    : beta : with C=1, this is irrelevant
     2.27    : b_DA : with C=1, this is irrelevant
     0.00    :  1.77 :    : esp
     2.59    : c_DA  : with esp = 0, this is irrelevant
     @@@gamma   : gamma

 : Potential part
  @@@vij_cont  : Vij_const, in kcal/mol
    0         : if contains Vij_ex part

[off_diagonal.end]

: ----------------------------------------------------------------------------

[off_diagonal.start.H3O_GLU-D]

  PT : Type of coupling: Proton Transfer
  2 6  : evb_index of DONOR atom (should be in molecule A)
  1 1  : evb_index of ACCEPT atom (should be in molecule B)
  2 7  : evb_index of HYDROGEN atom (should be in molecule B)

  : A_Rq Type : A(R,q) = f(R) * g(q)
  2 : 1-symmetric; 2-asymmetric

  : parameters
     @@@r0_sc  : r0_sc
     @@@lambda : lambda
     0.00    : R0_DA
     1.00    : C  setting to 1.00 makes only the gaussian effective
     @@@arq_alp    : alpha
     @@@a_da    : a_DA
     0.00    : beta : with C=1, this is irrelevant
     2.27    : b_DA : with C=1, this is irrelevant
     0.00    :  1.77 :    : esp
     2.59    : c_DA  : with esp = 0, this is irrelevant
     @@@gamma    : gamma

 : Potential part
  @@@vij_cont  : Vij_const, in kcal/mol
    0     : if contains Vij_ex part

[off_diagonal.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

[segment.end]


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
:::S                                                                      S:::
:::S   SEGMENT:   REPULSIVE TERMS                                         S:::
:::S                                                                      S:::
:::SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS:::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
[segment.repulsive]
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef GLU

[repulsive.start.GLU-D]

Hydronium : H3O

:::::::::::::::::::::::::::::::::::::::::::

: The parameters

H3O  : EVB_Type of H3O
OC   : Atom_Type of GLU

: ----------------------------------------------------------------------------

 @@@voo_b  : 0.125313  : B
 0.138908  : b
 2.394032  : b'
 2.400000  : d_OO
 @@@voh_c  : C
 @@@voh_lc : c
 @@@d_oh   : 1.000000  : d_OH

: cutoff for OO
 2.722230   3.274360

: cutoff for OH
@@@oh_cutl  4.00

[repulsive.end]

[repulsive.start.GLU-P]

Expon2 : Gaussian like repulsive terms V_rep = Vii + B exp[ b (R_DA - b_DA)^2 ]

GLU-P : EVB_Type of center

: The parameters

@@@vii  :: constant Vii

1 : Number of pairs: 1

OH1 : type D
HH : type A
@@@vb   : B
@@@vlb  : b
@@@bda  : b_DA
2.50    : cut-off

[repulsive.end]

#endif

: ----------------------------------------------------------------------------
: ----------------------------------------------------------------------------

#ifdef WAT

[repulsive.start.H3O]

Hydronium : MS-EVB3

:::::::::::::::::::::::::::::::::::::::::::

: Parameters for MS-EVB3

H3O  : EVB_Type of H3O
OW   : Atom_Type of OW

9.917841      : B
1.102152      : b
2.006625      : b'
2.400000      : d_OO
5.091732      : C
8.992002      : c
1.000000      : d_OH

: cutoff for OO
2.587470  2.979440

: cutoff for OH
1.591925  2.594177

[repulsive.end]

#endif

[segment.end]

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
