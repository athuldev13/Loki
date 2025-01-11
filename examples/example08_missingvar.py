# encoding: utf-8
"""
example08_missingvar.py

Input variable checking.

Learn how loki responds when a variable you requested 
is missing from the input file. 

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

# Define a missing variable
# -------------------------
# To show you how loki informs you if a variable you 
# requested doesn't exist in your input files, let's 
# define a variable that clearly doesn't exist: 
taus.add_var("missing","missing","A missing variable").add_view(1,0.,1.)

# Try and plot it 
# ---------------
h = Hist(sample=sample, xvar=taus.missing.get_view(), sel=taus.baseline)
p = Plot("MyDangerousPlot",[h])
processor = Processor() 
processor.draw_plots([p])

# you should receive an error message 

## EOF
