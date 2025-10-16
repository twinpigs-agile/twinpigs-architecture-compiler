#!/bin/bash

source ./_build_stages.sh


echo "Building ${PROGRAM_VERSION}"
export PROGRAM_VERSION

create_venv
set_version
activate_venv
install_requirements
prepare_gettext
build_msgs
run_tests
run_mypy
run_linter
pyinstaller_build
build_samples
