#from ROOT import *
#ROOT.gROOT.LoadMacro("AtlasStyle.C") 
#SetAtlasStyle()

## Will: fixing up broken python implementation
import os, ROOT
dir = '%s' % os.path.dirname(os.path.abspath(__file__))
ROOT.gROOT.LoadMacro(os.path.join(dir,"AtlasStyle.C")) 
