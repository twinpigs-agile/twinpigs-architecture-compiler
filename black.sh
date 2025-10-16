#!/bin/bash
source ./_build_stages.sh
activate_venv
run_black
exit 0
