#!/bin/bash

export PCDS_CONDA_VER=6.0.1
source /cds/group/pcds/pyps/conda/pcds_conda 

launcher="$(realpath $0)"
export LAUNCHER_DIR="$(dirname ${launcher})"
app="${LAUNCHER_DIR}/homs_overview/mirrorScreen.py"

pydm --hide-menu-bar --hide-nav-bar -m $1 ${app} &
