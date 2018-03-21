[main]
tpl_file = tests/test_data/fill_tpl/production_cpu_pbs.tpl, tests/test_data/fill_tpl/production_inp.tpl
filled_tpl_name = {output_name}.job, {output_name}.inp
out_dir = tests/test_data/fill_tpl/
[tpl_vals]
job_name = {name}
runtime = {runtime}
structure = test.psf
coordinates = test.pdb
input_name = {input_name}
output_name = {output_name}
[tpl_equations]
walltime = int({runtime}*15)
run = {runtime}*500000
