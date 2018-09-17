cv molid top
cv configfile /Users/xadams/PycharmProjects/md_utils/tests/test_data/CV_analysis/orientation_quat.in
set start 0
set basename [lindex $argv 0]
set file [open "${basename}_quat.log" w]
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