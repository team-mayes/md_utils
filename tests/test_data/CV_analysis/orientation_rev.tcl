cv molid top
cv configfile /home/xadams/bin/orientation_rev.in
set basename "orientation"
set file [open "${basename}_rev.log" w]
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
