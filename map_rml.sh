#!/bin/bash

rml_dir="gbad/schema/authority"
ttl_dir="gbad/mapping/target"

rml=$(find "$rml_dir" -type f -name "*.rml")
rml_filename=$(basename "$rml" .rml)
ttl="$ttl_dir/mapped_$rml_filename.ttl"

java -jar rmlmapper* -s turtle -m "$rml" -o "$ttl"
