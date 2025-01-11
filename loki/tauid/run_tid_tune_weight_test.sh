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
DOCHECKS=1
LOKI="loki"
PRONG="1P"
EFF="45"

## Flattening Config
DIR="/Users/wedavey/Data/MxAOD/THORtrain/v1"
if [ "${PRONG}" == "1P" ]; then 
    FSEL="--sel TauJets.baseline1P"
else
    FSEL="--sel TauJets.baseline3P"
fi
VARFILE="vars.txt"
FVARS="--fvars ${VARFILE}"

## Tuning Config
FDISC="--disc TauJets.BDTJetScore:fine"
FXVAR="--xvar TauJets.pt:weight"
FYVAR="--yvar TauJets.mu:tid"
FSELFLAT="--sel=nocut"

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
TauJets.isTauFlags
#EventInfo.truth_resonance_mass
TauJets.decayMode
TauJets.decayModeTruth" > ${VARFILE} 
fi
}

decorate_all(){
FIN=$1
FOUT=`echo $FIN | sed "s:.root:_deco.root:g"`
${LOKI} ntup wp ${FIN}  -c tune_${PRONG}_ws_2D.root  -w "NewTight_ws_2D:${EFF}"  -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx1_2D.root -w "NewTight_wx1_2D:${EFF}" -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx2_2D.root -w "NewTight_wx2_2D:${EFF}" -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_unw_2D.root -w "NewTight_unw_2D:${EFF}" -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_ws_1D.root  -w "NewTight_ws_1D:${EFF}"  -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx1_1D.root -w "NewTight_wx1_1D:${EFF}" -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_wx2_1D.root -w "NewTight_wx2_1D:${EFF}" -o ${FOUT} --usehist
${LOKI} ntup wp ${FOUT} -c tune_${PRONG}_unw_1D.root -w "NewTight_unw_1D:${EFF}" -o ${FOUT} --usehist
}


## Baseline
create_vars

# flatten
if [ ! -e "sig${PRONG}_ws.root" ]; then 
    echo "Producing flat ntup: sig${PRONG}_ws.root..."
    ${LOKI} ntup flat -d ${DIR} -s DYtautau_ws ${FSEL} ${FVARS} -o sig${PRONG}_ws.root --useweight
fi

# tune
echo
echo "Running baseline tuning"
${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} -o tune_${PRONG}_ws_2D.root -t 0.${EFF}

# decorate
echo 
echo "Running baseline decoration"
${LOKI} ntup wp sig${PRONG}_ws.root -c tune_${PRONG}_ws_2D.root -w "NewTight_ws_2D:${EFF}" -o sig${PRONG}_ws_deco.root --usehist

# compare
echo 
echo "Producing baseline comparisons"
${LOKI} wpplot sig${PRONG}_ws_deco.root --wps "${IDBASE},NewTight_ws_2D"
mkdir plots_baseline; mv *.png canvases.root plots_baseline/.


## Weigthing Tests
if [ ${DOCHECKS} -eq 1 ]; then
    # flatten
    echo "Producing alternate weighting samples"
    if [ ! -e "sig${PRONG}_wx1.root" ]; then
        ${LOKI} ntup flat -d ${DIR} -s DYtautau_wx1 ${FSEL} ${FVARS} -o sig${PRONG}_wx1.root --useweight &> log.flat_wx1 &
    fi
    if [ ! -e "sig${PRONG}_wx2.root" ]; then
        ${LOKI} ntup flat -d ${DIR} -s DYtautau_wx2 ${FSEL} ${FVARS} -o sig${PRONG}_wx2.root --useweight &> log.flat_wx2 &
    fi
    if [ ! -e "sig${PRONG}_unw.root" ]; then
        ${LOKI} ntup flat -d ${DIR} -s DYtautau_unw ${FSEL} ${FVARS} -o sig${PRONG}_unw.root --useweight &> log.flat_unw 
    fi
   
    # tune 
    echo
    echo "Running alternate tunings"
    ${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname sig${PRONG}_wx1.root ${FSELFLAT} -o tune_${PRONG}_wx1_2D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname sig${PRONG}_wx2.root ${FSELFLAT} -o tune_${PRONG}_wx2_2D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} ${FYVAR} --fname sig${PRONG}_unw.root ${FSELFLAT} -o tune_${PRONG}_unw_2D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} --fname sig${PRONG}_ws.root ${FSELFLAT} -o tune_${PRONG}_ws_1D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} --fname sig${PRONG}_wx1.root ${FSELFLAT} -o tune_${PRONG}_wx1_1D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} --fname sig${PRONG}_wx2.root ${FSELFLAT} -o tune_${PRONG}_wx2_1D.root -t 0.${EFF}
    ${LOKI} tune ${FDISC} ${FXVAR} --fname sig${PRONG}_unw.root ${FSELFLAT} -o tune_${PRONG}_unw_1D.root -t 0.${EFF}

    # decorate
    decorate_all sig${PRONG}_ws.root
    decorate_all sig${PRONG}_wx1.root
    decorate_all sig${PRONG}_wx2.root
    decorate_all sig${PRONG}_unw.root

    # compare
    ${LOKI} wpplot sig${PRONG}_ws_deco.root --wps "${IDBASE},NewTight_ws_2D,NewTight_wx1_2D,NewTight_wx2_2D,NewTight_unw_2D"
    mkdir plots_v1_ws_2D; mv *.png canvases.root plots_v1_ws_2D
    ${LOKI} wpplot sig${PRONG}_wx1_deco.root --wps "${IDBASE},NewTight_ws_2D,NewTight_wx1_2D,NewTight_wx2_2D,NewTight_unw_2D"
    mkdir plots_v2_wx1_2D; mv *.png canvases.root plots_v2_wx1_2D
    ${LOKI} wpplot sig${PRONG}_wx2_deco.root --wps "${IDBASE},NewTight_ws_2D,NewTight_wx1_2D,NewTight_wx2_2D,NewTight_unw_2D"
    mkdir plots_v3_wx2_2D; mv *.png canvases.root plots_v3_wx2_2D
    ${LOKI} wpplot sig${PRONG}_unw_deco.root --wps "${IDBASE},NewTight_ws_2D,NewTight_wx1_2D,NewTight_wx2_2D,NewTight_unw_2D"
    mkdir plots_v4_unw_2D; mv *.png canvases.root plots_v4_unw_2D
    ${LOKI} wpplot sig${PRONG}_ws_deco.root --wps "${IDBASE},NewTight_ws_1D,NewTight_wx1_1D,NewTight_wx2_1D,NewTight_unw_1D"
    mkdir plots_v5_ws_1D; mv *.png canvases.root plots_v5_ws_1D
    ${LOKI} wpplot sig${PRONG}_wx1_deco.root --wps "${IDBASE},NewTight_ws_1D,NewTight_wx1_1D,NewTight_wx2_1D,NewTight_unw_1D"
    mkdir plots_v6_wx1_1D; mv *.png canvases.root plots_v6_wx1_1D
    ${LOKI} wpplot sig${PRONG}_wx2_deco.root --wps "${IDBASE},NewTight_ws_1D,NewTight_wx1_1D,NewTight_wx2_1D,NewTight_unw_1D"
    mkdir plots_v7_wx2_1D; mv *.png canvases.root plots_v7_wx2_1D
    ${LOKI} wpplot sig${PRONG}_unw_deco.root --wps "${IDBASE},NewTight_ws_1D,NewTight_wx1_1D,NewTight_wx2_1D,NewTight_unw_1D"
    mkdir plots_v8_unw_1D; mv *.png canvases.root plots_v8_unw_1D

    # weighting scheme plots
    python ${SCRIPT}
    mkdir plots_weighting; mv *.png canvases.root plots_weighting/.

fi

# EOF
