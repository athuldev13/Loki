#!/bin/bash
#--------------------------------------------------------------
# train_tid.sh 
# ~~~~~~~~~~~~
# This script tests a basic tau ID training setup, as described
# in the documentation. 
#
# The input sample directory can be selected by modifying 'DIR'
#
# TODO: either make DIR and DOCHECKS passed as arguments, or 
#       wrap up in a loki command
#--------------------------------------------------------------

## General Config
LOKI="loki"
#DIR="/Volumes/PhysicsEmergency/Data/MxAOD/THORr207/v1"
DIR="/Users/wedavey/Data/MxAOD/THORtrain/v1"
VARFILE="vars.txt"

## create vars function
create_vars(){
if [ ! -e "${VARFILE}" ]; then
echo "\
TauJets.centFrac
TauJets.etOverPtLeadTrk
TauJets.innerTrkAvgDist
TauJets.absipSigLeadTrk
TauJets.SumPtTrkFrac
TauJets.ChPiEMEOverCaloEME
TauJets.EMPOverTrkSysP
TauJets.ptRatioEflowApprox
TauJets.mEflowApprox" > ${VARFILE} 
fi
}


## Execute 
# flatten
echo "Creating flat ntups: sig.root, bkg.root..."
${LOKI} ntup flat -d ${DIR} -s DYtautau -o sig.root &> log.sig &
${LOKI} ntup flat -d ${DIR} -s Multijet -o bkg.root --notruth &> log.bkg

# split 1p/3p
echo "Splitting sig.root into sig1P.root and sig3P.root..."
${LOKI} ntup skim sig.root --sel TauJets.mode1P -o sig1P.root &> log.sig1P
${LOKI} ntup skim sig.root --sel TauJets.mode3P -o sig3P.root &> log.sig3P
echo "Splitting bkg.root into bkg1P.root and bkg3P.root..."
${LOKI} ntup skim bkg.root --sel TauJets.mode1P -o bkg1P.root &> log.bkg1P
${LOKI} ntup skim bkg.root --sel TauJets.mode3P -o bkg3P.root &> log.bkg3P

# weight 
echo "Applying pt weight to background samples..."
${LOKI} ntup weight bkg1P.root sig1P.root -o bkg1P_weight.root &> log.bkg1P_weight
${LOKI} ntup weight bkg3P.root sig3P.root -o bkg3P_weight.root &> log.bkg3P_weight

# split train/test
echo "Splitting into training and testing samples..."
${LOKI} ntup split sig1P.root --fout1 sig1P_train.root --fout2 sig1P_test.root &> log.sig1Ptrain_test
${LOKI} ntup split bkg1P_weight.root --fout1 bkg1P_weight_train.root --fout2 bkg1P_weight_test.root &> log.bkg1Ptrain_test

# train
echo "Training new 1P classifier..."
create_vars
${LOKI} train sig1P_train.root bkg1P_weight_train.root -n MyFirstBDT --fvars vars.txt --fixoutliers --args "NTrees=100" &> log.train

# decorate
echo "Decorating new 1P classifier..."
${LOKI} ntup deco sig1P_test.root --tmva "MyFirstBDT:MyFirstBDT.xml" -o sig1P_test_deco.root &> log.sig1P_test_deco
${LOKI} ntup deco bkg1P_weight_test.root --tmva "MyFirstBDT:MyFirstBDT.xml" -o bkg1P_weight_test_deco.root &> log.bkg1P_weight_test_deco

# compare
echo "Making comparison plots..."
${LOKI} mvaplot sig1P_test_deco.root bkg1P_weight_test_deco.root --vars TauJets.BDTJetScore,MyFirstBDT &> log.compare

# EOF
