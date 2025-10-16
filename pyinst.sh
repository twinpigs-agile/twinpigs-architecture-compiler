#!/bin/bash

source ./_build_stages.sh


echo "Running pyinstaller ${PROGRAM_VERSION}"

set_version
activate_venv
pyinstaller_build
