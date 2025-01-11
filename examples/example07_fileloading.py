# encoding: utf-8
"""
example07_fileloading.py

Learn how to use FileHandler to easily load input files for 
your samples. 

Covers: 
* loki.core.file.FileHandler

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
from loki.core.file import FileHandler
# loki common/config 
from loki.common import samples
from loki.tauid import plots as tauid_plots
# file transfer 
from config import get_samples_dir


# Setup loki framework
# --------------------
setup()

# Select a sample from the samples module
# ---------------------------------------
sample = samples.Gammatautau

# Configure input file(s) for your sample
# ---------------------------------------
# In this case 'get_samples_dir()' will prepare 
# a mock-up of the input samples path structure 
# expected by loki. The structure is: 
#     <path>/<dataset>/<files>
#
# The <path> can contain a collection of <dataset>s, 
# and typically a new <path> is made for each THOR
# production. Each <dataset> may contain multiple 
# <file>s. 
#  
# An example being sometihng like this: 
# loki_samples_v1
# loki_samples_v1/dataset1/
# loki_samples_v1/dataset1/ntuple1.root
# loki_samples_v1/dataset2/
# loki_samples_v1/dataset2/ntuple1.root
# loki_samples_v1/dataset2/ntuple2.root
# ...
#
# Check-out the structure of the new directory: 
#     loki_samples_v1
# that is created after running this example.
#  
# FileHandler will search through the sub-directories
# of the data_path matching the name (or a regex) 
# to the samples.  
data_path = get_samples_dir()
FileHandler(data_path, [sample])

# Make some plots
# ---------------
plots = tauid_plots.create_eff_profiles_wrt_truth(sample,prongs=1)
processor = Processor(ncores=10, event_frac=0.01, usecache=False)
processor.draw_plots(plots)

## EOF
