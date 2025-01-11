# encoding: utf-8
"""
example02_hist.py

How to create your own histogram, plot it on a canvas
producing a png and save it to a ROOT file. 

Also describes how to choose and apply existing variables
and selection criteria, and how to define your own.

Covers:
* loki.core.hist.Hist
* loki.core.process.Processor
* loki.core.plot.Plot
* loki.core.file.OutputFileStream
* loki.common.samples
* loki.common.vars
* loki.common.cuts

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
from loki.core.hist import Hist
from loki.core.plot import Plot
from loki.core.file import OutputFileStream
# loki common/config 
from loki.common import samples, vars, cuts
from loki.common.vars import taus
# file transfer 
from config import get_file1

# setup loki framework
setup()

# select a sample from the samples module
sample = samples.Gammatautau

# configure input file(s) for your sample
sample.files = [get_file1()]

# Choose variable to plot
# -----------------------
# Variables are typically associated to a Container
# (eg. taus, truetaus, event), reflecting the structure
# of the MxAODs. You can browse the list of defined 
# variables in loki.common.vars 
# 
# You can also create your own variables using the 
# Container.add_var(<var>,...) and add_expr(<var>,...) 
# functions. These attach the new variable to the 
# container so it can be accessed via: 
#     container.<var>
#
# Variables can be assigned 'Views', representing
# a particular binning choice. When creating a 
# histogram the view must be selected using 
# VarBase.get_view(<view>). If view name isn't provided
# the default view will be selected.

var = taus.numTrack.get_view()

# Choose selection to apply 
# -------------------------
# Most RootDrawable objects support application 
# of selection. Individual selection criteria can 
# be defined using the add_var() and add_expr() 
# functions, analogous to adding new variables. 
# Multiple selection criteria can be grouped 
# using the Container.add_cuts() function.
# 
# Existing selection criteria can be found in 
# loki.common.cuts. Make sure to import the 
# module if you want the criteria to be added 
# to the Containers. 
# 
# Analogously to the variables, you can define 
# your own selection criteria. It is also possible 
# to combine cuts via:      
#     cut = cut1 & cut2

sel = taus.baseline

# Define a histogram
# ------------------
h = Hist(sample=sample,
         xvar=var,
         sel=sel)
# Note: Hist derives from loki.core.hist.RootDrawable, which is the 
# fundamental building block for all plots in loki. Other objects
# deriving from the same base class are EffProfile, ResoProfile...
# The common base class provides a common way to interact with 
# RootDrawable objects, eg they can all be added to a Plot or 
# saved to an output file. The difference is just in how the 
# underlying ROOT object is constructed.  

# Process the histogram
# ---------------------
# This creates the underlying ROOT object (eg. TH1 in this case)
processor = Processor(usecache=False) 
processor.process(h)

# you can directly access the underlying ROOT object like this: 
h.rootobj().Draw()
# however, in practise you rarely need to do this since loki 
# provides functionality to interact with your RootDrawable object

# IMPORTANT: h.rootobj() is NOT AVAILABLE before the histogram 'h' 
# is processed by the Processor.

# eg. lets add the histogram to a plot and generate a pdf
p = Plot("MyFirstPlot",[h])
p.draw()

# or lets write the hist to a file
ofstream = OutputFileStream("hists.root")
ofstream.write(h)

## EOF
