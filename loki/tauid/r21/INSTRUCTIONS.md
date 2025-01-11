# Instructions for training the R21 Tau-ID

## Prepare samples

To prepare the samples necessary for training and testing use the
`prepare_sample.sh` script:

    source prepare_sample.sh <path to MxAODs> <output directory for processed samples>

This script assumes the training is done with Gammatautau samples for signal and
dijet samples (mass slices from JZ1W to JZ6W) for background. This script uses
the variables, binnings etc. defined in `defs.py`. The MxAODs that were used for
R21 Tau-ID training can be found on EOS:

    /atlas/atlascerngroupdisk/perf-tau/MxAODs/StreamMain/v07/v07-01


## Training of the R21 Tau-ID

For the remainder of the steps the script `run.py` is used. It defines
various actions:

- `all`: Performs all actions
- `spawn-bdt`: Creates the algorithms defining the training setup
- `train-bdt`: Trains the algorithms that were previously spawned
- `deco-bdt`: Decorates the BDT scores onto the testing samples
- `tune-wp`: Extracts the flat working points from the decorated score
- `deco-wp`: Decorates the flattened score and the predefined working points onto the ntuples

which can be accessed via the command line e.g.

    python r21.py all --indir samples/ --outdir samples/

Most actions take `--indir` and `--outdir` arguments to specify the directories
where the required inputs (e.g. samples, trained algorithms, ...) are saved and
the directory where the outputs of the action will be stored. If not specified
everything will be set to the current working directory.

