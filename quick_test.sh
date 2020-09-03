#!/usr/bin/env bash

# Directory variables
scripts_dir=$(dirname $(realpath ${0}))
parent_out_dir=${scripts_dir}/tests.results

# File variables
mk_design=${scripts_dir}/mk_design.py
log=${scripts_dir}/test.log
err=${scripts_dir}/test.err

# Arrays
template_designs=( jpy.notebooks/design.test.csv
  jpy.notebooks/design.test.no_extra_text.csv
  jpy.notebooks/design.test.csv
  jpy.notebooks/design.test.no_extra_text.csv
  jpy.notebooks/design.test.csv
  jpy.notebooks/design.test.no_extra_text.csv
  jpy.notebooks/design.test.csv
  jpy.notebooks/design.test.no_extra_text.csv )

out_dirs=( grp_design
  grp_design_no_ext_text
  grp_design_no_covs
  grp_design_no_ext_text_no_covs
  grp_design_demean_age
  grp_design_no_ext_text_demean_age 
  grp_design_demean_multi-col
  grp_design_no_ext_text_demean_multi-col )

des_covs=( "1,2,3,4,5,6"
  "1,2,3,4,5,6"
  "3,4"
  "3,4"
  "1,2,3,4,5,6"
  "1,2,3,4,5,6"
  "1,2,5,6"
  "1,2,5,6" )

# demean_cols=( ""
#   ""
#   ""
#   ""
#   "1"
#   "1"
#   "1,5,6"
#   "1,5,6" )

demean_cols=( ""
  ""
  ""
  ""
  "1"
  "1"
  "1,3,4"
  "1,3,4" )

rm_subs=( "sub-009,sub-023,sub-039"
  "9,23,39"
  "sub-009,sub-023,sub-039"
  "9,23,39"
  "sub-009,sub-023,sub-039"
  "9,23,39"
  "sub-009,sub-023,sub-039"
  "9,23,39" )

if [[ ${#out_dirs[@]} != ${#des_covs[@]} ]] && [[ ${#out_dirs[@]} != ${#demean_cols[@]} ]]; then
  echo ""
  echo "Uneven length arrays. Exiting..."
  # exit 1
else
  echo ""
  echo "All input arrays are of the same length. Proceeding with tests."
fi

# Run each test
for (( i=0; i < ${#out_dirs[@]}; i++ )); do
  # Print message
  echo ""
  echo "Running test: ${out_dirs[$i]}"

  echo "" >> ${log}
  echo "Running test: ${out_dirs[$i]}" >> ${log}

  # Make output directory
  out=${parent_out_dir}/${out_dirs[$i]}
  if [[ ! -d ${out} ]]; then
    mkdir -p ${out}
  fi

  # Get abspath for template file
  template_design=$(realpath ${template_designs[$i]})

  # Run test
  ${mk_design} --in=${template_design} --out=${out}/grp.design.test --rm-list="${rm_subs[$i]}" --ret-cols="${des_covs[$i]}" --demean="${demean_cols[$i]}" --sep="," >> ${log} 2>> ${log}

  # rename output information file to csv for easy checking
  mv ${out}/grp.design.test.all_info.txt ${out}/grp.design.test.all_info.csv
done

# Auxillary test for study design matrix
parent_out_dir=${scripts_dir}/tests.auxillary 
template_design=$(realpath jpy.notebooks/master.template.design.csv)

out_dirs=( design_sct_no_covs
  sct_adhd_parent_no_covs
  sct_adhd_teacher_no_covs
  sct_child_no_covs
  sct_parent_no_covs
  sct_teacher_no_covs
  design_sct_covs
  sct_adhd_parent_covs
  sct_adhd_teacher_covs
  sct_child_covs
  sct_parent_covs
  sct_teacher_covs 
  sct_child_parent_adhd_covs 
  sct_cci-2_parent_adhd_covs
  sct_cci-2_covs )

des_covs=( "3,4,5"
  "6,7" 
  "8,9" 
  "10"
  "6"
  "8" 
  "1,2,3,4,5" 
  "1,2,6,7"
  "1,2,8,9"
  "1,2,10"
  "1,2,6"
  "1,2,8" 
  "1,2,7,10" 
  "1,2,7,11" 
  "1,2,11" )

if [[ ${#out_dirs[@]} != ${#des_covs[@]} ]] && [[ ${#out_dirs[@]} != ${#demean_cols[@]} ]]; then
  echo ""
  echo "Uneven length arrays. Exiting..."
  # exit 1
else
  echo ""
  echo "All input arrays are of the same length. Proceeding with tests."
fi

for (( i=0; i < ${#out_dirs[@]}; i++ )); do
  # Print message
  echo ""
  echo "Running test: ${out_dirs[$i]}"

  echo "" >> ${log}
  echo "Running test: ${out_dirs[$i]}" >> ${log}

  # Make output directory
  out=${parent_out_dir}/${out_dirs[$i]}
  if [[ ! -d ${out} ]]; then
    mkdir -p ${out}
  fi

  # Run test
  ${mk_design} --in=${template_design} --out=${out}/grp.design.test --rm-list="sub-1013,sub-1515,sub-1569" --ret-cols="${des_covs[$i]}" --demean="1" --sep="," >> ${log} 2>> ${log}

  # rename output information file to csv for easy checking
  mv ${out}/grp.design.test.all_info.txt ${out}/grp.design.test.all_info.csv
done



echo ""
echo "Done!"
echo ""
