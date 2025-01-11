#!/bin/bash
# Prepares samples for R21 Tau-ID training
#
# Steps:
# - Flattening of MxAODs to ntuples
# - Skimming into 1- and 3-prong categories
# - Kinematic reweighting
# - Splitting into training and test samples
# - Skimming of outliers from the training samples
#
# Example call:
# source prepare_samples.sh <directory containing MxAODs> <output directory>

DIR="$(dirname "${BASH_SOURCE[0]}")"

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

# Flattening of MxAOD
loki -i $DIR/defs.py ntup flat -d $IN_DIR -s Gammatautau -o $OUT_DIR/sig.root
loki -i $DIR/defs.py ntup flat -d $IN_DIR -s Multijet -o $OUT_DIR/bkg.root --notruth

# Skimming
loki ntup skim $OUT_DIR/sig.root --sel TauJets.mode1P -o $OUT_DIR/sig1P.root
loki ntup skim $OUT_DIR/sig.root --sel TauJets.mode3P -o $OUT_DIR/sig3P.root
loki ntup skim $OUT_DIR/bkg.root --sel TauJets.mode1P -o $OUT_DIR/bkg1P.root
loki ntup skim $OUT_DIR/bkg.root --sel TauJets.mode3P -o $OUT_DIR/bkg3P.root

# pt flattening
cp $OUT_DIR/bkg1P.root $OUT_DIR/bkg1P_weight.root
cp $OUT_DIR/bkg3P.root $OUT_DIR/bkg3P_weight.root
loki -i $DIR/defs.py ntup weight $OUT_DIR/bkg1P_weight.root $OUT_DIR/sig1P.root \
    --var "TauJets.ptIntermediateAxis:reweight_r21"
loki -i $DIR/defs.py ntup weight $OUT_DIR/bkg3P_weight.root $OUT_DIR/sig3P.root \
    --var "TauJets.ptIntermediateAxis:reweight_r21"

# Splitting
loki ntup split $OUT_DIR/sig1P.root
loki ntup split $OUT_DIR/sig3P.root
loki ntup split $OUT_DIR/bkg1P_weight.root
loki ntup split $OUT_DIR/bkg3P_weight.root

# Skimming outliers from training sets
loki -i $DIR/defs.py ntup skim $OUT_DIR/sig1P_train.root \
    --sel TauJets.IDOutliers_common,TauJets.IDOutliers_1P \
    -o $OUT_DIR/sig1P_train_outl.root

loki -i $DIR/defs.py ntup skim $OUT_DIR/sig3P_train.root \
    --sel TauJets.IDOutliers_common,TauJets.IDOutliers_3P \
    -o $OUT_DIR/sig3P_train_outl.root

loki -i $DIR/defs.py ntup skim $OUT_DIR/bkg1P_weight_train.root \
    --sel TauJets.IDOutliers_common,TauJets.IDOutliers_1P \
    -o $OUT_DIR/bkg1P_weight_train_outl.root

loki -i $DIR/defs.py ntup skim $OUT_DIR/bkg3P_weight_train.root \
    --sel TauJets.IDOutliers_common,TauJets.IDOutliers_3P \
    -o $OUT_DIR/bkg3P_weight_train_outl.root

