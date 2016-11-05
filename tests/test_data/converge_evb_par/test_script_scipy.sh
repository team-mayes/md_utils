#!/usr/bin/env bash

input_file=$1
val_1=$(grep 'constant Vii' ${input_file} | awk '{print $1}')
val_2=$(grep 'Vij_const' ${input_file} | awk '{print $1}')
val_3=$(grep 'gamma' ${input_file}  | awk '{print $1}')
echo "${val_1}^2+(${val_2}-2.0)^2+${val_3}^2" | bc -l

