#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "${SCRIPT_DIR}"/venv/bin/activate
export PYTHONPATH=${PYTHONPATH}:"${SCRIPT_DIR}"

# The dataframe cache is in the working directory, so cd to the
# script directory to re-use the cache.
cd "${SCRIPT_DIR}"
python3 "${SCRIPT_DIR}"/custom_forecast/app.py --host=0.0.0.0
