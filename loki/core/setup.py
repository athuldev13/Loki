# encoding: utf-8
"""
loki.core.setup
~~~~~~~~~~~~~~~

This module provides global setup for the loki framework

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


## modules
import logging
from time import localtime, asctime
import ROOT
from loki.core.helpers import print_logo, set_palette
from loki.core.logger import log



# - - - - - - - - - - function defs - - - - - - - - - - - - #
#____________________________________________________________
def setup(
        log_level   = None, 
        batch_mode  = True,
        atlas_style = True,
        suppress_root_msgs = True,
        suppress_root_errors = True,
        ):
    """Global setup for loki framework   

    :param log_level: logging output level
    :type log_level: logging.LEVEL (eg. DEBUG, INFO, WARNING...)
    :param batch_mode: toggle ROOT.SetBatch()
    :type batch_mode: bool
    :param atlas_style: set the ATLAS figure style
    :type atlas_style: bool
    :param suppress_root_msgs: suppress logging output of WARNING or lower from ROOT
    :type suppress_root_msgs: bool
    
    """
    # log level
    if log_level == None: log_level = logging.INFO
    log().setLevel(log_level)
    
    # aweseom logo
    print_logo()  
    
    # Suppress ROOT output  
    ROOT.gROOT.SetBatch(batch_mode)
    if suppress_root_msgs: 
        ROOT.gErrorIgnoreLevel = 3000
    if suppress_root_errors:
        ROOT.gErrorIgnoreLevel = 4000

    # style
    if atlas_style:
        from loki.atlasstyle import AtlasStyle 
        ROOT.SetAtlasStyle() 
    ROOT.gStyle.SetPaintTextFormat('2.1f')
    set_palette("orange")
    
    # get this show rolling    
    log().info(f"Starting Job: {asctime(localtime())}")
        
    pass


## EOF
