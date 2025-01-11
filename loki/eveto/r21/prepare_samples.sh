#!/bin/bash
# Assumes loki is set up
#
# Usage: 
#   prepare_samples.sh <MxAOD IN DIR> <OUT DIR>
#
#
# Example IN DIR: /eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/StreamMain/v02/v02-00
#
set -e

# Config 
ETAREGS="EtaBar EtaEnd1 EtaEnd23"
DIR="$(dirname "${BASH_SOURCE[0]}")"
DEFS="${DIR}/defs.py"
VARSELE="${DIR}/vars_ele.txt"
VARSTAU="${DIR}/vars_tau.txt"

## Parse Command line args
if [ -z "$1" ]
then
    echo "No MxAOD input directory given"
    exit 1
fi

if [ -z "$2" ]
then
    echo "No output directory given"
    exit 1
fi
IN_DIR=$1
OUT_DIR=$2

mkdir -p ${OUT_DIR}

# Flattening
loki -i ${DEFS} ntup flat -d ${IN_DIR} -s Gammatautau -o ${OUT_DIR}/sig.root --fvars ${VARSTAU} --sel TauJets.evetoTAU
loki -i ${DEFS} ntup flat -d ${IN_DIR} -s DYee        -o ${OUT_DIR}/bkg.root --fvars ${VARSELE} --sel TauJets.evetoELE

# Prepare Dirs
for REG in ${ETAREGS}; do 
    mkdir -p ${OUT_DIR}/${REG}
    
    # Skim Eta Region
    loki -i ${DEFS} ntup skim ${OUT_DIR}/sig.root --sel TauJets.trk${REG},TauJets.mode1P -o ${OUT_DIR}/${REG}/sig.root
    loki -i ${DEFS} ntup skim ${OUT_DIR}/bkg.root --sel TauJets.trk${REG},TauJets.mode1P -o ${OUT_DIR}/${REG}/bkg.root

    # pt-reweight
    loki -i ${DEFS} ntup weight ${OUT_DIR}/${REG}/bkg.root ${OUT_DIR}/${REG}/sig.root --var "TauJets.ptGeV:weight"
    loki -i ${DEFS} qp "TauJets.ptGeV:weight" ${OUT_DIR}/${REG}/sig.root ${OUT_DIR}/${REG}/bkg.root --norm
    mv *.png ${OUT_DIR}/${REG}/.

    # Split test/train
    loki -i ${DEFS} ntup split ${OUT_DIR}/${REG}/sig.root 
    loki -i ${DEFS} ntup split ${OUT_DIR}/${REG}/bkg.root 
done




