# encoding: utf-8
"""
example10_mva.py

IMPORTANT: you must run example09_flatntup.py before this example

How to train a BDT with TMVA  

Note: command-line utils are now available for mva training, see: 

    https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/training.html

Covers: 
* loki.train.algs

More details on the functionality of the classes can be found at:  

    https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/py-modindex.html

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-07-24"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
# loki core
from loki.core.setup import setup
from loki.core.sample import Sample
from loki.train.algs import TMVAClassifier
from loki.train.ntup import skim_ntup
# loki common/config 
from loki.common import vars, cuts, styles
taus = vars.taus


# Setup loki framework
# --------------------
setup()



# Create signal and background samples
# ------------------------------------
# Classifier training requires you have
# separate signal and background samples.
# They must have only one input file each,
# and must not have duaghters.
# Let's create them from the flat ntuple
# we created in the previous exercise.
fin = "ntup.root"
fsig = "sig.root"
fbkg = "bkg.root"
skim_ntup(fin, fsig, sel=taus.mode1P0NTruth)
skim_ntup(fin, fbkg, sel=taus.mode1P1NTruth)


# Configure input samples
# -----------------------
# Must configure signal and background samples.
# A weight can be provided, which is typically
# combined into a single variable called "weight"
# in the FlatNtupWriter, accessible via vars.weight.
weight = None
# uncomment if you want to use the event weight from the ntup flattener
#weight = vars.weight
sig = Sample(name="Signal",     files=[fsig], weight=weight, sty=styles.Signal)
bkg = Sample(name="Background", files=[fbkg], weight=weight, sty=styles.Background)


# Configure common preselection
# -----------------------------
sel = taus.barrel

# Configure input variables
# ------------------------- 
tidvars = [
    taus.etOverPtLeadTrk,
    taus.absipSigLeadTrk,
    taus.dRmax,
    taus.ChPiEMEOverCaloEME,
    taus.EMPOverTrkSysP,
    taus.ptRatioEflowApprox,
    taus.mEflowApprox,
    taus.centFrac,
    taus.innerTrkAvgDist,
    taus.SumPtTrkFrac,
    ]
 
# Configure your BDT
# ------------------
# Configure your classifier type, training samples and
# input variables. BDT options can be provided via 'algopts',
# which are  passed to TMVA. TMVA Factory options can
# be provided via factopts.
# see loki.train.algs for details
#
# You must also save your alg as a workspace before
# you can train. Then all the training output is
# stored in the workspace.
alg = TMVAClassifier(tmvatype="BDT", sig_train=sig, bkg_train=bkg,
                     invars=tidvars, algopts={"NTrees":2000, "MaxDepth":4})

alg.saveas("MyFirstAlg.alg")

# Train, Test, Evaluate, Dominate
# -------------------------------
alg.train()

# The results can be viewed in root with: 
# TMVA::TMVAGui( "MyFirstAlg.alg/aux/TMVA.root" );

## EOF