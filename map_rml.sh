#!/bin/bash

rml_dir="gbad/schema/authority"
ttl_root="gbad/mapping/target"

rml=$(find "$rml_dir" -type f -name "*.rml")
rml_filename=$(basename "$rml" .rml)

ttl_dir="$ttl_root/$rml_filename"
mkdir -p "$ttl_dir"
ttl="$ttl_dir/mapped.ttl"

java -jar rmlmapper* -s turtle -m "$rml" -o "$ttl"
