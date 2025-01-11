# encoding: utf-8
"""
example01_basics.py

Basic introductory example. 

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
# loki common/config 
from loki.common import samples
from loki.tauid import plots as tauid_plots
# file transfer 
from config import get_file1


# Setup loki framework
# --------------------
setup()

# Select a sample from the samples module
# ---------------------------------------
sample = samples.Gammatautau

# Configure input file(s) for your sample
# ---------------------------------------
# In this case 'get_file1()' will retrieve 
# the input file for this example from AFS 
# and then return its path. A more 
# sophisticated treatment is given in a 
# later tutorial  
sample.files = [get_file1()]

# Get some pre-defined plots
# --------------------------
plots = tauid_plots.create_eff_profiles_wrt_truth(sample,prongs=1)
# Note: at this stage the physical plots don't actually exist. 
# Rather, each plot represents a set of details (or instructions).  
# To actually build the plots they must be passed to a processor.

# Process the plots
# -----------------
processor = Processor(usecache=False) 
processor.draw_plots(plots)

## EOF
