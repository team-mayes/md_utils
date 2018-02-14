mol top 0
set prot [atomselect top "protein"]
puts "Enter a filename:"
set name [gets stdin]
set com [measure center $prot]
$prot moveby [vecinvert $com]
$prot writepdb $name.pdb 
$prot delete
exit
