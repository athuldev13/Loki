# encoding: utf-8
"""
example04_efficiencies.py

How to plot profiles of variables, efficiencies and resolutions.
How to fit your profiles.  

Covers: 
* loki.core.hist.Profile
* loki.core.hist.EffProfile
* loki.core.hist.ResoProfile
* loki.core.hist.Fit

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
from loki.core.hist import Profile, EffProfile, ResoProfile, Fit
from loki.core.plot import Plot
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

# Create Profiles
# ---------------
# select the dependent variable for our profiles
depvar = taus.ptGeV.get_view("low")

# choose baseline selection criteria for profiles
sel = taus.baseline1P

# 1 - Variable Profile
# Create a profile of the tau RNNJetScore variable
rnnscore = taus.RNNJetScore.get_view()
prof_rnn = Profile(name="h_rnn", sample=sample, xvar=depvar, yvar=rnnscore, sel=sel)
plot_rnn = Plot("MyFirstVariableProfile",[prof_rnn])

# 2 - Efficiency Profile
# Create a tau ID efficiency profile.  
# Need to define the numerator/denominator selection 
# (in this case for the 1-prong Medium ID efficiency)
sel_pass  = sel & taus.medium
prof_eff = EffProfile(name="h_eff", sample=sample, xvar=depvar, sel_pass=sel_pass, sel_total=sel)
plot_eff = Plot("MyFirstEfficiencyProfile",[prof_eff])

# 3 - Resolution Profile
# Create tau pt resolution profile
resvar = taus.ptRes.get_view()
prof_reso = ResoProfile(name="h_reso", sample=sample, xvar=depvar, yvar=resvar, mode="core", sel=sel)
plot_reso = Plot("MyFirstResolutionProfile",[prof_reso])
 
# 4 - Fit Profile
# Fit the RNN profile with a linear function
# Note: you can fit any 1D RootDrawable 
fit = Fit(prof_rnn,"[0] + [1]*x",sty=styles.fit) 
plot_fit = Plot("MyFirstProfileFit",[prof_rnn,fit])


# Process and save the plots
# --------------------------
# The Processor interface register/process/draw_plots can 
# take lists of plots for your convenience
processor = Processor()
plots = [plot_rnn, plot_eff, plot_reso, plot_fit]  
processor.draw_plots(plots)
ofstream = OutputFileStream("profplots.root")
ofstream.write(plots)


## EOF
