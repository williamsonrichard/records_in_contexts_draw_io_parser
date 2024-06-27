#!/bin/bash

# originally generated with ChatGPT-3.5 on the date this was committed,
# with modifications

# initial prompt:
# write a shell bash script that uses find to look for *.ttl files in a particular dir and all subdirs, then copies them to another given dir and prints the message how many files were copied; with both input and output dir hardcoded in script, so it doesn't take arguments
#
# some follow-up prompt:
# i have a bash forloop copying $file to $output_dir. write code for implementing additional logic: if the name of file starts with regex "([cdf]|rg)[ _-]*\d", then cp not to root $output_dir but to "$output_dir/description-listings", elseif starts with  regex "[abc]a[ _-]*\d", then cp not to root $output_dir but to "$output_dir/authority", else cp to root $output_dir. regex are case insensitive

# Define input directory
input_dir="gbad"

# Define the subdirectories to exclude
exclude_subdirs=("schema" "mapping" "transform" "validate")

# Build the find command
find_command="find \"$input_dir\" -type f -name \"*.ttl\""

# Add each exclude subdirectory to the find command
for exclude_subdir in "${exclude_subdirs[@]}"; do
    find_command+=" -not -path \"$input_dir/$exclude_subdir/*\""
done

# Use find to search for *.ttl files in the input directory and its subdirectories, excluding the specified subdirectories
echo "Collecting files: $find_command"
ttl_files=$(eval $find_command)

# Define output directory
output_dir="../gbad-project.github.io/gbad/from_draw_io_parser"

description_listings_dir="$output_dir/description-listings"
authority_dir="$output_dir/authority"

# Ensure the subdirectories exist
mkdir -p "$description_listings_dir"
mkdir -p "$authority_dir"

# Initialize a counter for copied files
copied_files=0

# Loop through each found *.ttl file
for file in $ttl_files; do
    filename=$(basename "$file")

    # Check if the filename matches the first regex
    if [[ "$filename" =~ ^([cdf]|rg)[\ _-]*[0-9] ]]; then
        cp "$file" "$description_listings_dir"
        echo "Copied $filename to $description_listings_dir"
    
    # Check if the filename matches the second regex
    elif [[ "$filename" =~ ^[abc]a[\ _-]*[0-9] ]]; then
        cp "$file" "$authority_dir"
        echo "Copied $filename to $authority_dir"
    
    # Otherwise, copy to the root output directory
    else
        cp "$file" "$output_dir"
        echo "Warning! Authority or description? Check manually. Copied $filename to $output_dir"
    fi

    # Increment the counter
    ((copied_files++))
done

# Print the number of copied files
echo "Copied $copied_files files from '$input_dir' to '$output_dir'."
