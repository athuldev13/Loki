#!/bin/bash

# config
export LOKIDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
UTILDIR=${LOKIDIR}/scripts

# add Loki to PYTHONPATH
echo "Adding ${LOKIDIR} to PYTHONPATH..."
if [ -z "${PYTHONPATH}" ]; then
    PYTHONPATH="${LOKIDIR}"
else
    PYTHONPATH="${LOKIDIR}:${PYTHONPATH}"
fi

# add utils to PATH
echo "Adding ${UTILDIR} to PATH..."
if [ -z "${PATH}" ]; then
    PATH="${UTILDIR}"
else
    PATH="${UTILDIR}:${PATH}"
fi




