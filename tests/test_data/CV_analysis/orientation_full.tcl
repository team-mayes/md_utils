# this tcl script outputs orientational quaternions for the C and N domain of XylE
# requires eq.pdb as a reference
cv molid top
cv configfile /home/xadams/bin/orientation_full_double.in
set basename "orientation"
set file [open "${basename}_full.log" w]
puts -nonewline $file [cv printframelabels]
set n [expr {int([molinfo top get numframes])}]
for {set i 0 } { $i < $n } { incr i } {
    cv frame $i
    cv update
    set angles [cv printframe]
    puts -nonewline $file $angles
    unset angles
}
close $file
cv delete
exit
