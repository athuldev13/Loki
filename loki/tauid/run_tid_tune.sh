#!/bin/bash
#--------------------------------------------------------------
# run_tid_tune.sh
# ~~~~~~~~~~~~~~~
# This script executes example tunings for a 45% tau ID efficiency. 
# The efficiency is flattened against tau pt (in MeV!) and mu.  
#
# The input sample directory can be selected by modifying 'DIR'
#
# Additional checks can be switched on by setting 'DOCHECKS=1'
#
# Number of prongs can be specified by PRONG ('1P' or '3P')
#
# TODO: either make DIR and DOCHECKS passed as arguments, or 
#       wrap up in a loki command
#--------------------------------------------------------------

## General Config
DOCHECKS=0
LOKI="loki -i hacks.py"
#LOKI="loki"
#PRONG="1P"
#EFF="60"
PRONG="3P"
EFF="42"

## Flattening Config
#DIR="/Users/wedavey/Data/MxAOD/THORtrain/v1"
DIR="/Volumes/PhysicsEmergency/Data/MxAOD/THORr207/v8"
GGHDIR="/Volumes/PhysicsEmergency/Data/MxAOD/THORr207/v10"
if [ "${PRONG}" == "1P" ]; then 
    FSEL="--sel TauJets.baseline1P"
    FSELBKG="--sel TauJets.baseline1PNoTruth"
else
    FSEL="--sel TauJets.baseline3P"
    FSELBKG="--sel TauJets.baseline3PNoTruth"
fi
VARFILE="vars.txt"
VARFILEBKG="vars_bkg.txt"
FVARS="--fvars ${VARFILE}"
FVARSBKG="--fvars ${VARFILEBKG}"

## Tuning Config
FDISC="--disc TauJets.BDTJetScore:fine"
FDISCUNCORR="--disc TauJets.uncorrBDT:fine"
FXVAR="--xvar TauJets.pt:weight"
FYVAR="--yvar TauJets.mu:tid"
FSELFLAT="--sel=nocut"
FSMOOTH="--smooth2D k5a"

FDOHIST="--usehist"
#FDOHIST=""

## Comparison Config
IDBASE="TauJets.tight"
SCRIPT="${LOKIDIR}/loki/tauid/weight_comparisons_tid.py"


# create vars function
create_vars(){
if [ ! -e "${VARFILE}" ]; then
echo "\
TauJets.pt
TauJets.ptFinalCalib
TauJets.ptTruth
TauJets.eta
TauJets.nVtx
TauJets.mu
TauJets.BDTJetScore
TauJets.uncorrBDT
TauJets.isTauFlags
#EventInfo.truth_resonance_mass
TauJets.decayMode
TauJets.decayModeTruth" > ${VARFILE} 
fi
}

create_vars_bkg(){
if [ ! -e "${VARFILEBKG}" ]; then
echo "\
TauJets.pt
TauJets.ptFinalCalib
#TauJets.ptTruth
TauJets.eta
TauJets.nVtx
TauJets.mu
TauJets.BDTJetScore
TauJets.uncorrBDT
TauJets.isTauFlags
#EventInfo.truth_resonance_mass
TauJets.decayMode
#TauJets.decayModeTruth" > ${VARFILEBKG} 
fi
}


decorate_all(){
FIN=$1
FOUT=`echo $FIN | sed "s:.root:_deco.root:g"`
${LOKI} ntup wp ${FIN}  -c tune_${PRONG}_ws_2D.root  -w "NewTight_ws_2D:${EFF}"  -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx1_2D.root -w "NewTight_wx1_2D:${EFF}" -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx2_2D.root -w "NewTight_wx2_2D:${EFF}" -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_unw_2D.root -w "NewTight_unw_2D:${EFF}" -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_ws_1D.root  -w "NewTight_ws_1D:${EFF}"  -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx1_1D.root -w "NewTight_wx1_1D:${EFF}" -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx2_1D.root -w "NewTight_wx2_1D:${EFF}" -o ${FOUT} ${FDOHIST}
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_unw_1D.root -w "NewTight_unw_1D:${EFF}" -o ${FOUT} ${FDOHIST}
}


## Baseline
create_vars
create_vars_bkg
 
# flatten
if [ ! -e "sig${PRONG}_ws.root" ]; then 
    echo "Producing flat ntup: sig${PRONG}_ws.root..."
    ${LOKI} ntup flat -d ${DIR} -s DYtautau_ws ${FSEL} ${FVARS} -o sig${PRONG}_ws.root --useweight
fi
if [ ! -e "bkg${PRONG}_ws.root" ]; then 
    echo "Producing flat ntup: bkg${PRONG}_ws.root..."
    ${LOKI} ntup flat -d ${DIR} -s Multijet_ws ${FSELBKG} ${FVARSBKG} -o bkg${PRONG}_ws.root --useweight
fi

# tune
echo
echo "Running tuning"
${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} ${FSMOOTH} -o tune_${PRONG}_ws_2D.root 
${LOKI} tune ${FDISC} ${FXVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} ${FSMOOTH} -o tune_${PRONG}_ws_1D.root
${LOKI} tune ${FDISCUNCORR} ${FXVAR} ${FYVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} ${FSMOOTH} -o tune_${PRONG}_ws_2D_uncorr.root
${LOKI} tune ${FDISCUNCORR} ${FXVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} ${FSMOOTH} -o tune_${PRONG}_ws_1D_uncorr.root

# decorate
echo 
echo "Running decoration"
# sig 
${LOKI} ntup wp sig${PRONG}_ws.root -c tune_${PRONG}_ws_2D.root -w "NewTight2D${PRONG}:${EFF}" -o sig${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp sig${PRONG}_ws_deco.root -c tune_${PRONG}_ws_1D.root -w "NewTight1D${PRONG}:${EFF}" -o sig${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp sig${PRONG}_ws_deco.root -c tune_${PRONG}_ws_2D_uncorr.root -w "NewTight2Duncorr${PRONG}:${EFF}" -o sig${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp sig${PRONG}_ws_deco.root -c tune_${PRONG}_ws_1D_uncorr.root -w "NewTight1Duncorr${PRONG}:${EFF}" -o sig${PRONG}_ws_deco.root ${FDOHIST}
# bkg
${LOKI} ntup wp bkg${PRONG}_ws.root -c tune_${PRONG}_ws_2D.root -w "NewTight2D${PRONG}:${EFF}" -o bkg${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp bkg${PRONG}_ws_deco.root -c tune_${PRONG}_ws_1D.root -w "NewTight1D${PRONG}:${EFF}" -o bkg${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp bkg${PRONG}_ws_deco.root -c tune_${PRONG}_ws_2D_uncorr.root -w "NewTight2Duncorr${PRONG}:${EFF}" -o bkg${PRONG}_ws_deco.root ${FDOHIST}
${LOKI} ntup wp bkg${PRONG}_ws_deco.root -c tune_${PRONG}_ws_1D_uncorr.root -w "NewTight1Duncorr${PRONG}:${EFF}" -o bkg${PRONG}_ws_deco.root ${FDOHIST}

# compare
echo 
echo "Producing baseline comparisons"
${LOKI} wpplot sig${PRONG}_ws_deco.root --wps "${IDBASE},NewTight2D${PRONG},NewTight1D${PRONG},NewTight2Duncorr${PRONG},NewTight1Duncorr${PRONG}"
mkdir plots_uncorr${PRONG}; mv *.png canvases.root plots_uncorr${PRONG}/.
${LOKI} wpplot bkg${PRONG}_ws_deco.root --wps "${IDBASE},NewTight2D${PRONG},NewTight1D${PRONG},NewTight2Duncorr${PRONG},NewTight1Duncorr${PRONG}" --bkg
mkdir plots_uncorr_bkg${PRONG}; mv *.png canvases.root plots_uncorr_bkg${PRONG}/.

# flat bdt
#${LOKI} ntup wp sig${PRONG}_ws_deco.root -c tune_${PRONG}_ws_2D_uncorr.root -w "FlatBDT2Duncorr${PRONG}" -o sig${PRONG}_ws_deco.root ${FDOHIST} --trans & 
#${LOKI} ntup wp bkg${PRONG}_ws_deco.root -c tune_${PRONG}_ws_2D_uncorr.root -w "FlatBDT2Duncorr${PRONG}" -o bkg${PRONG}_ws_deco.root ${FDOHIST} --trans
#${LOKI} mvaplot sig${PRONG}_ws_deco.root bkg${PRONG}_ws_deco.root --vars "FlatBDT2Duncorr${PRONG},TauJets.uncorrBDT"
#mkdir plots_flatmva_${PRONG}; mv *.png canvases.root plots_flatmva_${PRONG}/.
# EOF
