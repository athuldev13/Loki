#!/bin/bash

# workflow for double-staged mva training
#========================================
# Mail  : richard.frank.hartmann@cern.ch
#
# - works with: loki-00-02-05 and THOR-00-00-18,
#   but needs local modifications
# - input variables can be specified in a text file standard_set.txt
# - local input samples:
samplePath="/ZIH.fast/users/duschi/TauTracking/training_input_revert/"
#   /ZIH.fast/users/duschi/TauTracking/train_split_layer_0_revert/

startdate=`date +%s`
echo "================================================"
echo "   Starting mva training using THOR and loki!"
echo "================================================"
echo "---"

# general config
if [[ $PYTHONPATH != *loki* ]]
then
    echo "--- No loki set up!"
    exit 1
elif [[ $PATH != *ATLAS* ]]
then
    echo "--- No THOR set up!"
    exit 1
elif [ ! -e standard_set.txt ]
then
    echo "--- No input variables specified. Take default set of variables!"
    cat <<EOF > standard_set.txt
TauTracks.jetSeedPt
TauTracks.trackEta
TauTracks.z0sinThetaTJVA
TauTracks.rConv
TauTracks.rConvII
TauTracks.dRJetSeedAxis
TauTracks.d0
TauTracks.qOverP
TauTracks.numberOfInnermostPixelLayerHits
TauTracks.numberOfPixelSharedHits
TauTracks.numberOfSCTSharedHits
TauTracks.numberOfTRTHits
TauTracks.eProbabilityHT
TauTracks.nPixHits
TauTracks.nSiHits
EOF
fi

echo "--- Choose directory name:"
read tPath
while [ -d $tPath ]
do
    echo "--- Directory already exists. Choose different name:"
    read tPath
done

mkdir $tPath
cd $tPath
mkdir step1
mkdir step2
cp ../standard_set.txt ./
cp ../standard_set.txt step1/
cp ../standard_set.txt step2/
cp ../standard_set.txt step2/standard_set_flagSet.txt
echo "TauTracks.flagSet" >> step2/standard_set_flagSet.txt

# first step
cd step1

# needed setup for local samples
for j in TT CT IT FT
do
    mkdir $j
    for i in `ls /ZIH.fast/users/duschi/TauTracking/train_split_layer_0_revert/$j`
    do
	mkdir $j/$i
	ln -s /ZIH.fast/users/duschi/TauTracking/train_split_layer_0_revert/$j/$i $j/$i/$i
    done
done

echo "---"
echo "--- Producing ntuple:"
for i in TT CT IT FT
do
    nice -n 19 loki ntup flat -d ./$i -s DYtautau_unw -o $i.root --fvars standard_set.txt --notruth --sel nocut
done

echo "---"
echo "--- Merging ntuples:"
nice -n 19 hadd -f TT-CT.root TT.root CT.root
nice -n 19 hadd -f IT-FT.root IT.root FT.root
cd ../

echo "---"
echo "--- Train BDT:"
nice -n 19 loki train step1/TT-CT.root step1/IT-FT.root --fvars standard_set.txt --wsig noweight --wbkg noweight -n TT-CT_vs_IT-FT > log_train1
inWeight_0=`pwd`"/TT-CT_vs_IT-FT.xml"
treshold_0=`getMaxSignificance.py TT-CT_vs_IT-FT_plots.root | cut -d ' ' -f 2`

# second step
cd step2
echo "---"
echo "--- Create xAODs depending on first training:"

for i in TT CT FT
do
    nice -n 19 RunMxAODCreator.py MxAODTrackingSplit --jo_options "tracktype=$i;run_layer_1=True;InputWeightsPath_0=$inWeight_0;Threshold_0=$treshold_0" -i $samplePath -o $i -f 0.5 > log_$i 2>&1
done
nice -n 19 RunMxAODCreator.py MxAODTrackingSplit --jo_options "tracktype=IT;run_layer_1=True;InputWeightsPath_0=$inWeight_0;Threshold_0=$treshold_0" -i $samplePath -o IT -f 0.5 > log_IT 2>&1

for i in TT IT FT CT
do
    for j in `ls $i`
    do
        mkdir $i/${j%.root}/
        mv $i/$j $i/${j%.root}/$j
    done
done

echo "---"
echo "--- Producing ntuple:"
for i in TT CT IT FT
do
    nice -n 19 loki ntup flat -d ./$i -s DYtautau_unw -o $i.root --fvars standard_set_flagSet.txt --notruth --sel nocut
done
cd ../

echo "---"
echo "--- Train BDTs:"
nice -n 19 loki train step2/TT.root step2/CT.root --fvars standard_set.txt --wsig noweight --wbkg noweight --sel 'TauTracks.reco_TT' -n TT_vs_CT > log_train2_1
nice -n 19 loki train step2/IT.root step2/FT.root --fvars standard_set.txt --wsig noweight --wbkg noweight --sel 'TauTracks.reco_IT' -n IT_vs_FT > log_train2_2
treshold_0_0=`getMaxSignificance.py TT_vs_CT_plots.root | cut -d ' ' -f 2`
treshold_0_1=`getMaxSignificance.py IT_vs_FT_plots.root | cut -d ' ' -f 2`
echo "--- cut 0  :" $treshold_0
echo "--- cut 0_0:" $treshold_0_0
echo "--- cut 0_1:" $treshold_0_1

enddate=`date +%s`
diff=$[$enddate - $startdate]
printf 'Execution time: %s:%02d:%02d h\n' "$[$diff / 3600]" "$[($diff % 3600)/60]" "$[$diff % 60]"

# EOF
