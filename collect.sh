#!/bin/bash

# originally generated with ChatGPT-3.5 on the date this was committed,
# with modifications

# initial prompt:
# write a shell bash script that uses find to look for *.ttl files in a particular dir and all subdirs, then copies them to another given dir and prints the message how many files were copied; with both input and output dir hardcoded in script, so it doesn't take arguments

# Define input directory
input_dir="gbad"

# Define the directory to exclude
exclude_subdir="schema"

# Construct the full path of the directory to exclude
exclude_dir="${input_dir}/${exclude_subdir}"

# Define output directory
output_dir="../gbad-project.github.io/gbad/from_draw_io_parser"

# Use find to search for *.ttl files in the input directory and its subdirectories, excluding the specified directory
ttl_files=$(find "$input_dir" -type f -name "*.ttl" -not -path "$exclude_dir/*")

# Initialize a counter for copied files
copied_files=0

# Loop through each found *.ttl file
for file in $ttl_files; do
    # Copy the file to the output directory
    cp "$file" "$output_dir/"
    # Increment the counter
    ((copied_files++))
done

# Print the number of copied files
echo "Copied $copied_files files from '$input_dir' to '$output_dir'."
