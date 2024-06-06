#!/bin/bash

# originally generated with ChatGPT-4o on the date this was committed,
# with modifications
#
# initial prompt:
#
# write bash script for this
#
# cat "gbad/person/Orville Wood Authority.drawio" | python draw_io_parser.py -o http://gbad.archives.gov.on.ca/schema/authority# -p http://gbad.archives.gov.on.ca/ -m url > gbad/person/orville_wood_authority.owl
#
# in this command, the "gbad/person/Orville Wood Authority.drawio" has to be given as an argument, -o and -p arguments are fixed, and the output file is named such that it is saved in the same dir as input file and the filename is constructed using lower case capitalization and underscores as shown
#
# notable follow-up prompt:
#
# also add support for optional supplying arguments to the draw_io_parser.py script through this bash script. for example, so that i could write something like:
#
# ./process_drawio.sh "gbad/person/Orville Wood Authority.drawio" -p http://example.com -o http://example.com/ontology# -m ' '='[space]'

# Function to display usage
usage() {
  echo "Usage: $0 <input_drawio_file> [optional commands for the parser]"
  exit 1
}

# Check if an argument is provided
if [ -z "$1" ]; then
  usage
fi

# Get the input file path
input_file="$1"
shift

# Check if the input file exists
if [ ! -f "$input_file" ]; then
  echo "Input file not found: $input_file"
  exit 1
fi

# Construct the output file path
output_file_dir=$(dirname "$input_file")
output_file_name=$(basename "$input_file" .drawio | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -d "()[]/,:.\"'").owl
output_file="$output_file_dir/$output_file_name"

# Construct the TTL file path
ttl_file="$output_file_dir/$(basename "$output_file" .owl).ttl"

# Function to properly escape and quote arguments
quote_argument() {
    local quoted_arg
    quoted_arg=$(printf "%q" "$1")
    echo "$quoted_arg"
}

# Collect remaining arguments as optional commands for the parser
optional_commands=()
for arg in "$@"; do
    optional_commands+=( "$(quote_argument "$arg")" )
done

# Check if optional_commands is empty and set it to a particular value if empty
if [ ${#optional_commands[@]} -eq 0 ]; then
    optional_commands="-m url \
                       -o http://gbad.archives.gov.on.ca \
                       -p http://gbad.archives.gov.on.ca/"
fi

# Construct the python command
python_command="cat \"$input_file\" | python draw_io_parser.py ${optional_commands[@]} > \"$output_file\""

# Print the output message
echo "Executing command: $python_command"

# Run the parser script
eval $python_command

# Print the output message
echo "Manchester OWL Output saved to: $output_file"

# Convert the OWL file to TTL
robot_sh_path="./robot.sh"
conversion_command="$robot_sh_path convert -i \"$output_file\" -o \"$ttl_file\""

# Print the conversion command
echo "Executing command: $conversion_command"

# Run the conversion command
eval $conversion_command

# Print the output message
echo "TTL Output saved to: $ttl_file"
