cv molid top
cv configfile /home/xadams/bin/orientation_reverse.in
set start 0
set basename "orientation"
set file [open "${basename}_reverse.log" w]
puts -nonewline $file [cv printframelabels]
set n [expr {int([molinfo top get numframes])}]
for {set i $start } { $i < $n } { incr i } {
    cv frame $i
    cv update
    set angles [cv printframe]
    puts -nonewline $file $angles
    unset angles
}
close $file
cv delete
exit
