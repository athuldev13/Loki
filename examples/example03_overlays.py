# encoding: utf-8
"""
example03_overlays.py

How to overlay multiple RootDrawable objects, style them, 
plot them, save them to file. 

Covers: 
* loki.core.style.Style
* loki.core.hist.Ratio (and ratio plots)
* loki.common.styles

More details on the functionality of the classes can be found at:  

    https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/py-modindex.html

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-29"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
# loki core
from loki.core.setup import setup
from loki.core.process import Processor
from loki.core.hist import Hist, Ratio
from loki.core.plot import Plot
from loki.core.style import Style
from loki.core.logger import log
from loki.core.file import OutputFileStream
# loki common/config 
from loki.common import samples, vars, cuts, styles
from loki.common.vars import taus
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

# Create Overlay Plot
# -------------------
# Let's create a plot with 2 histograms. 
# In this case, lets plot the Tau RNN score 
# separately for 1-prong and 3-prong taus. 

# select the variable to plot
var = taus.RNNJetScore.get_view()

# define the selection for each histogram
sel1P = taus.baseline1P
sel3P = taus.baseline3P

# --> Style your histograms: 
# (either choose an existing style from loki.common.styles
# or create your own using loki.core.style.Style)
# Note: samples already have their own default style, so if you are 
# overlaying conributions from differernt samples (eg. signal vs 
# background) you don't need to explicitly set the style for each
sty1P = Style("1P",tlatex="1-prong",LineColor=styles.red,
              MarkerColor=styles.red,MarkerStyle=styles.fullcircle)
sty3P = Style("3P",tlatex="3-prong",LineColor=styles.blue,
              MarkerColor=styles.blue,MarkerStyle=styles.fullsquare)

# define histograms
h1P = Hist(name="h1P",sample=sample,xvar=var,sel=sel1P,sty=sty1P,normalize=True)
h3P = Hist(name="h3P",sample=sample,xvar=var,sel=sel3P,sty=sty3P,normalize=True)

# define plot (can be done before processing hists, for convenience)
p = Plot("MyFirstOverlay",[h1P,h3P])

# Create Ratio Plot
# -----------------
# now you made an overlay, what about adding ratios of the overlayed 
# root drawables in a panel below them main overlay? 
pratio = Plot("MyFirstRatio",[h1P,h3P], doratio=True)
# OMG, really? It was that easy?!?!?

# Note: ratios of RootDrawable objects can be constructed outside 
# of Plot. See loki.core.hist.Ratio 

# Process the plot
# ----------------
# process all inputs for the plot and draw canvas all in one go.
# Note: the Processor interface register/process/draw_plots can 
# all take lists of plots for your convenience
processor = Processor()  
processor.draw_plots([p,pratio])

# lets write the plot and inputs hists to the sub-directory "awesome" in plots.root
ofstream = OutputFileStream("plots.root")
ofstream.write([p,pratio],"awesome")


## EOF
