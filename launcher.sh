#!/bin/bash

# Uncomment and set to the latest version to freeze dependency
export PCDS_CONDA_VER=5.9.0
source /cds/group/pcds/pyps/conda/pcds_conda

launcher="$(realpath $0)"
export launcher_dir="$(dirname ${launcher})"
app="${launcher_dir}/homs_overview/homs_overview.py"

pydm --hide-nav-bar ${app} $@ # Can add pydm args here
