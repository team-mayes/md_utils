import subprocess

def call_vmd(psf,pdb,script,name):
    subprocess.call(["/Applications/VMD 1.9.3.app/Contents/Resources/VMD.app/Contents/MacOS/VMD", "-e", script, "-dispdev", "text", psf, pdb])


PSF="../tests/test_data/call_vmd/open_xylose.psf"
PDB="../tests/test_data/call_vmd/open_xylose.pdb"
SCRIPT="../../../bin/tcl_scripts/prot.tcl"
NAME="hello"
call_vmd(PSF,PDB,SCRIPT,NAME)
# subprocess.call(["/Applications/VMD 1.9.3.app/Contents/Resources/VMD.app/Contents/MacOS/VMD", "-e", "../../../bin/tcl_scripts/prot.tcl", "-dispdev", "text", "../tests/test_data/call_vmd/open_xylose.psf", "../tests/test_data/call_vmd/open_xylose.pdb"])
