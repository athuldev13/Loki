# Instructions for training the R21 Tau-ID

## Prepare samples

To prepare the samples necessary for training and testing use the
`prepare_sample.sh` script:

    source prepare_sample.sh <path to MxAODs> <output directory for processed samples>

For the R21 EleBDT training, the following input MxAOD path was used:

    /eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/StreamMain/v02/v02-00

This script assumes the training is done with Gammatautau samples for 
signal and DYee samples (mass slices including low-mass Zee and all 
high-mass DYee samples) for background. This script uses the variables, 
binnings etc. defined in `defs.py`.



## Training of the R21 EleBDT

For the remainder of the steps the script `run.py` is used. It defines
various actions:


- `spawn-bdt`: Creates the algorithms defining the training setup
- `train-bdt`: Trains the algorithms that were previously spawned
- `deco-bdt`: Decorates the BDT scores onto the testing samples
- `merge`: Merges ntuples from different eta regions
- `tune-wp`: Extracts the flat working points from the decorated score
- `deco-wp`: Decorates the flattened score and the predefined working points onto the ntuples
- `all`: Performs all above actions
- `plot-bdt`: Makes performance plots for bdt training (deco-bdt must be complete)
- `plot-wp`: Makes performance plots for working point tuning (deco-wp must be complete)

which can be accessed via the command line e.g.

    python r21.py -m spawn-bdt

Paths for the input/output ntuple dirs and the alg dir can be specified via the
`--indir`, `--outdir` and `--algdir` options. If not specified, everything will 
be set to the current working directory.