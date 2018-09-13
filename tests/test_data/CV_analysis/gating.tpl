# Global Parameters
colvarsTrajFrequency 1000

colvar {{
    name extracellular
    distance {{
        group1 {{
            psfSegID PROA PROA PROA
            atomNameResidueRange {{ CA 28-34 }}
            atomNameResidueRange {{ CA 58-63 }}
            atomNameResidueRange {{ CA 178-183 }}
        }}
        group2 {{
            psfSegID PROA PROA PROA
            atomNameResidueRange {{ CA 295-301 }}
            atomNameResidueRange {{ CA 315-320 }}
            atomNameResidueRange {{ CA 423-428 }}
        }}
    }}
}}

colvar {{
    name intracellular
    distance {{
        group1 {{
            psfSegID PROA PROA PROA
            atomNameResidueRange {{ CA 75-80 }}
            atomNameResidueRange {{ CA 148-154 }}
            atomNameResidueRange {{ CA 160-166 }}
        }}
        group2 {{
            psfSegID PROA PROA PROA
            atomNameResidueRange {{ CA 332-337 }}
            atomNameResidueRange {{ CA 391-397 }}
            atomNameResidueRange {{ CA 404-410 }}
        }}
    }}
}}
