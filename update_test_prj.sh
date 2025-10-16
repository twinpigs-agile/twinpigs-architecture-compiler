#!/bin/bash

source ./_build_stages.sh
activate_venv

echo "Updating the test project to the current compiler state"
pushd puml_compiler/src
python puml2graphml.py tests/projects/prj_01/source.puml tests/projects/prj_01/compiled.graphml
check_res_and_popd_on_exit
sed -i 's/tests\///g' tests/projects/prj_01/compiled.graphml
check_res_and_popd_on_exit
popd
