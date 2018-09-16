# Global Parameters
colvarsTrajFrequency 1000

colvar {{
    name alphas
    cartesian {{
        atoms {{
            psfSegID PROA PROA 
            atomNameResidueRange {{ CA 8-220 }}
            atomNameResidueRange {{ CA 276-463 }}
#        centerReference on
#        rotateReference on
#        refPositionsFile /pylon5/mc562gp/adamsa/common/eq_100ns.pdb
        }}
    }}
}}
