# encoding: utf-8
"""
example06_roc.py

How to plot ROC curves.  

Covers: 
* loki.core.hist.ROCCurve

More details on the functionality of the classes can be found at:  

    https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/py-modindex.html

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-07-06"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
# loki core
from loki.core.setup import setup
from loki.core.process import Processor
from loki.core.hist import ROCCurve
from loki.core.plot import Plot
from loki.core.file import OutputFileStream
# loki common/config 
from loki.common import samples
from loki.common.cuts import taus
# file transfer 
from config import get_file1, get_bkg_file

# Setup loki framework
# --------------------
setup()

# Configure samples
# -----------------
# this time we also need to configure a background sample 
# we have chosen jetjet_JZ4W which contains multijet events 
sig = samples.Gammatautau
bkg = samples.jetjet_JZ4W
sig.files = [get_file1()]
bkg.files = [get_bkg_file()]


# Define ROC Plot
# ---------------
# A ROC plot is a plot of the background rejection (y-axis) 
# vs the signal efficiency (x-axis) for a given discriminating
# variable. In this case we'll look at the tau identification, 
# whose discriminating variable is the RNNJetScore.  
var = taus.RNNJetScore.get_view("fine")

# Define the selection for signal and background. 
# Note: for signal we require the candidates are 
# 'truth-matched', while for background (jets), 
# we do not. 
sel_sig = taus.baseline1P
sel_bkg = taus.baseline1PNoTruth

# define the ROC
roc = ROCCurve(sig,bkg,xvar=var,
               sel_sig=sel_sig, sel_bkg=sel_bkg,
               name="MyAwesomeROC")
p = Plot("MyFirstROCPlot",[roc],logy=True)

# Process the plot
# ----------------
processor = Processor()  
processor.draw_plots(p)
ofstream = OutputFileStream("rocplots.root")
ofstream.write(p)

## EOF
