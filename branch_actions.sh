#!/bin/bash
script_parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

source "$script_parent_path/env/bin/activate"
python3 "$script_parent_path/main.py"

