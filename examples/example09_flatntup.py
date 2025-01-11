# encoding: utf-8
"""
example09_flatntup.py

How to create a flat ntuple for a sample and a selection of variables.

Note: command-line utils are now available for ntuple flattening, see: 

    https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/training.html

Note: ``flatten_ntup()`` has replaced ``FlatNtupWriter`` (since loki-0.2.2)

Covers: 
* loki.train.ntup.flatten_ntup

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
from loki.core.file import FileHandler
from loki.train.ntup import flatten_ntup
# loki common/config 
from loki.common.vars import taus, event
from loki.common import samples, cuts, vars
# file transfer 
from config import get_file1


# Setup loki framework
# --------------------
setup()

# Select a sample
# ---------------
sample = samples.Gammatautau
sample.files = [get_file1()]
# Note: for real trainig you should use the full set of DYtautau samples:   
#sample = samples.DYtautau
#data_path = "/Users/wedavey/Data/MxAOD/ICHEP/v3_nominal"
#FileHandler(data_path, [sample])

# Define variables
# ----------------
# basic variables
invars = [ taus.numTrack,
           taus.decayMode,
           taus.numProngTruth,
           taus.decayModeTruth,
           taus.pt,
           taus.eta,
           taus.ptTruth,
           taus.etaTruth,
           event.mu,
           taus.nVtx,
           ]
# tau id variables 
# Note: v.var used since "tidvars" are "View" objects
# possibility to add more variables in the ntuples 
# invars += [v.var for v in vars.tidvars]

# Define selection
# ----------------
sel = taus.baseline

# Write flat ntup
# ---------------
flatten_ntup(sample,invars,sel=sel,fout="ntup.root")

## EOF
