#This tcl script writes sugar-protein distances to a file to check for sugar dissociating from the protein
set name [lindex $argv 0]
set file [open $name w]
#Select protein and sugar for CoM calculation
set prot [atomselect top protein]
set sug [atomselect top "resname BXYL BGLC"]
set frequency [lindex $argv 1]
set n [expr {int([molinfo top get numframes])/$frequency}]
#Measurements are taken every 100th frame
for { set i 0 } { $i <= $n } { incr i } {
    set current [expr {int($i*$frequency+1)}]
    animate goto $current
    set distance [veclength [vecsub [measure center $prot] [measure center $sug]]]
    puts $file $distance
}
close $file
exit
