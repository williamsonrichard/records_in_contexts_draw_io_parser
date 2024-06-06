#!/bin/bash

# originally generated with Gemini Free Version on the date this was committed,
# with modifications

# initial prompt:
# i have a particular shell bash script that has the following usage
#
# "Usage: $0 <input_drawio_file> [optional commands for the parser]"
#
# it also outputs some output file in the same dir as the input file. I want to modify the script so that it if not given any arguments, it would look in the folder where the script is stored as well as any nested folders for *.drawio files and pass them as <input_drawio_file> iteratively

# Path to your original script (replace with the actual path)
ORIGINAL_SCRIPT_PATH="./parse.sh"

# Get the script directory
# script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir="gbad"
exclude_dir="schema"

# Find all *.drawio files recursively in the script directory, excluding the specified subdirectory
drawio_files=$(find "$script_dir" -path "$script_dir/$exclude_dir" -prune -o -type f -name "*.drawio" -print)

# Check if any Draw.io files were found
if [[ -z "$drawio_files" ]]; then
  echo -e "\nError: No *.drawio files found in the '$script_dir' directory or its subdirectories."
  exit 1
fi

# Convert the find results into an array
readarray -t drawio_files_array <<< "$drawio_files"

# Get the total number of files
total_files=${#drawio_files_array[@]}

# Print the total number of files
echo -e "Total number of *.drawio files found: $total_files"

# Loop through each Draw.io file and call the original script
for i in "${!drawio_files_array[@]}"; do
  drawio_file="${drawio_files_array[$i]}"
  file_number=$((i + 1))

  if [[ ! -f "$drawio_file" ]]; then
    echo -e "\nWarning: Skipping '$drawio_file' as it's not a file."
    continue
  fi

  # Print message before processing
  echo -e "\nProcessing file $file_number of $total_files: $drawio_file"
  "$ORIGINAL_SCRIPT_PATH" "$drawio_file" "$@"  # Pass any remaining arguments
done

echo -e "\nFinished processing all Draw.io files."
