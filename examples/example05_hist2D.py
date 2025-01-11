# encoding: utf-8
"""
example05_hist2D.py

How to create a 2D histogram. 

Covers: 
* loki.core.hist.Hist

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
from loki.core.hist import Hist
from loki.core.plot import Plot
from loki.core.file import OutputFileStream
# loki common/config 
from loki.common import samples
from loki.common.cuts import taus
# file transfer 
from config import get_file1

# Setup loki framework
# --------------------
setup()

# Select a sample
# ---------------
sample = samples.Gammatautau

# Configure input file(s)
# -----------------------
sample.files = [get_file1()]

# Define 2D Hist and Plot
# -----------------------
# Note: all you have to do is provide a yvar
xvar = taus.ptGeV.get_view("low")
yvar = taus.RNNJetScore.get_view()
sel  = taus.baseline1P
h = Hist(sample=sample, xvar=xvar, yvar=yvar, sel=sel)
p = Plot("MyFirst2DPlot",[h])

# Process the plots
# -----------------
plots = [p]
processor = Processor(usecache=False)
processor.draw_plots(plots)
ofstream = OutputFileStream("hists.root")
ofstream.write(plots)

## EOF
