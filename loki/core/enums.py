# encoding: utf-8
"""
loki.common.enums
~~~~~~~~~~~~~~~~~

Definition of global enumerations. 

Further info at: https://svnweb.cern.ch/trac/atlasoff/browser/Event/xAOD/xAODTau/trunk/xAODTau/TauDefs.h

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"


# - - - - - - - - - - - enum defs  - - - - - - - - - - - - #
# Tau ID Bits 
# 26.05.21 updated from https://gitlab.cern.ch/atlas/athena/blob/master/Event/xAOD/xAODTau/xAODTau/TauDefs.h

EleRNNLoose             = 15
EleRNNMedium            = 16
EleRNNTight             = 17
JetRNNSigVeryLoose	= 28
JetRNNSigLoose          = 29
JetRNNSigMedium         = 30
JetRNNSigTight          = 31

# Decay Modes
Mode_1p0n = 0
Mode_1p1n = 1
Mode_1pXn = 2
Mode_3p0n = 3
Mode_3pXn = 4

# asci color codes
DEFAULT  = u'\x1b[39;49m'
BLUE     = u'\x1b[34m'
BLUEBOLD = u'\x1b[1;34m'
RED      = u'\x1b[31m'
REDBOLD  = u'\x1b[1;31m'
REDBKG   = u'\x1b[1;41;37m'
YELLOW   = u'\x1b[33m'
UNSET    = u'\x1b[0m'



## EOF
