#!/usr/bin/env bash

input_file=$1
val_1=$(grep -m 1 'constant Vii' ${input_file} | awk '{print $1}')
val_2=$(grep -m 1 'Vij_const' ${input_file} | awk '{print $1}')
val_3=$(grep -m 1 'gamma' ${input_file}  | awk '{print $1}')
result=$(echo "${val_1}^2+(${val_2}-2.0)^2+${val_3}^2" | bc -l)
echo ${result}
echo ${result} > script_output.txt
