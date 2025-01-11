# encoding: utf-8
"""
validation.py
~~~~~~~~~~~~~

<Description of module goes here...>

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2017-02-08"
__copyright__ = "Copyright 2017 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
from loki.common import vars, cuts
from loki.common.plotgen import create_eff_profiles, create_res_profiles
from loki.common.styles import *

from loki.core.file import FileHandler, OutputFileStream
from loki.core.process import Processor
from loki.core.sample import Sample
from loki.core.setup import setup
from loki.core.style import Style

taus = vars.taus
setup()

## Configuration
##================

## basic config
dirs = ["/Users/wedavey/Data/MxAOD/StreamMain/v09", # No decorations, Vanilla MC16
        #"/Users/wedavey/Data/MxAOD/StreamMain/v07", # TEST0 - MVA Trk, all decorations 
        #"/Users/wedavey/Data/MxAOD/StreamMain/v08", # TEST1 - Vanilla, all decorations
        #"/Users/wedavey/Data/MxAOD/StreamMain/v10", # TEST2 - Vanilla, No TID, all other decorations, 
        #"/Users/wedavey/Data/MxAOD/StreamMain/v11", # TEST3 - MVA Trk, No TID, all other decorations, 
        #"/Users/wedavey/Data/MxAOD/StreamMain/v12", # TEST4 - Vanilla, All algs on, setting EDM bits, TID using Will flattening,
        # 
        "/Users/wedavey/Data/MxAOD/StreamMain/v13", # TEST0 - MVA Trk, Final R21 setup
        ]

sname = "Gammatautau"
#maxevents = 100000
#maxevents = 50000
maxevents = 300000
prong_modes = ["1P", "3P"]
decay_modes = ["1P0N", "1P1N", "1PXN", "3P0N", "3PXN"]
rmin = 0.5
rmax = 1.5 
do_migration_effs = False
depvars = vars.depvars
depvars = [taus.ptTruthGeV.get_view("log"),  
           taus.absetaTruth.get_view(), 
           taus.mu.get_view(),
           ]

## configure samples
regex=f"*{sname}*"
ref = Sample("Ref",  regex=regex, sty=Style("Ref",  LineColor=black,MarkerColor=black,MarkerStyle=fullcircle))
FileHandler(dirs[0],  [ref])
# define up to 5 test sample styles
test_styles = [ \
    {"LineColor":red,     "MarkerColor":red,     "MarkerStyle":opencircle}, 
    {"LineColor":blue,    "MarkerColor":blue,    "MarkerStyle":opensquare},
    {"LineColor":green,   "MarkerColor":green,   "MarkerStyle":opentriup},
    {"LineColor":magenta, "MarkerColor":magenta, "MarkerStyle":opentridn},
    {"LineColor":orange,  "MarkerColor":orange,  "MarkerStyle":openstar},
    ]
tests = []
for i, d in enumerate(dirs[1:]):
    sname = f"Test{i}"
    #s = Sample(sname, regex=regex, sty=Style(sname, **test_styles[i]), maxevents=maxevents) 
    s = Sample(sname, regex=regex, sty=Style(sname, **test_styles[i]))
    FileHandler(d, [s])
    tests.append(s)
samples = [ref] + tests


## Plot Definition
##================
plots = []


## Efficiency
kweff = {"ymin":0, "ymax":1.2, "doratio":True, "rmin":rmin, "rmax":rmax}
sel1PTruth = taus.baseline & taus.mode1PTruth
sel1PReco  = sel1PTruth & taus.mode1P
sel3PTruth = taus.baseline & taus.mode3PTruth
sel3PReco  = sel3PTruth & taus.mode3P

# Reco
plots += create_eff_profiles(samples, depvars=depvars, tag="1PReco",   sel_total=sel1PTruth, sel_pass=sel1PReco, dir="reco", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="3PReco",   sel_total=sel3PTruth, sel_pass=sel3PReco, dir="reco", **kweff)

# 1-prong
plots += create_eff_profiles(samples, depvars=depvars, tag="1PLoose",  sel_total=sel1PReco,  sel_pass=sel1PReco & taus.loose,  dir="tid", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="1PMedium", sel_total=sel1PReco,  sel_pass=sel1PReco & taus.medium, dir="tid", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="1PTight",  sel_total=sel1PReco,  sel_pass=sel1PReco & taus.tight,  dir="tid", **kweff)

# 3-prong
plots += create_eff_profiles(samples, depvars=depvars, tag="3PLoose",  sel_total=sel3PReco,  sel_pass=sel3PReco & taus.loose,  dir="tid", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="3PMedium", sel_total=sel3PReco,  sel_pass=sel3PReco & taus.medium, dir="tid", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="3PTight",  sel_total=sel3PReco,  sel_pass=sel3PReco & taus.tight,  dir="tid", **kweff)

# EleRNN
plots += create_eff_profiles(samples, depvars=depvars, tag="1PEleRNNLoose",   sel_total=sel1PReco,  sel_pass=sel1PReco & taus.EleRNNLoose,   dir="eveto", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="1PEleRNNMedium",  sel_total=sel1PReco,  sel_pass=sel1PReco & taus.EleRNNMedium,  dir="eveto", **kweff)
plots += create_eff_profiles(samples, depvars=depvars, tag="1PEleRNNTight",   sel_total=sel1PReco,  sel_pass=sel1PReco & taus.EleRNNTight,   dir="eveto", **kweff)

# decay mode
kwdecay = {"ymin":0, "ymax":1.2, "doratio":True, "rmin":rmin, "rmax":rmax, "dir":"decaymode"}
for modeTruth in decay_modes:
    selTruth = taus.baseline & getattr(taus, f"mode{modeTruth}Truth")
    for modeReco in decay_modes:
        if not do_migration_effs and (modeReco != modeTruth): continue
        selReco = selTruth & getattr(taus, f"mode{modeReco}")
        tag = f"DecayMode_T{modeTruth}_R{modeReco}"
        plots += create_eff_profiles(samples, depvars=depvars, tag=tag, sel_total=selTruth, sel_pass=selReco, **kwdecay)

## Resolutions
kwres = {"ymin":0, "doratio":True, "rmin":rmin, "rmax":rmax, "dir":"resolution"}
for mode in prong_modes + decay_modes:
    sel =  taus.tes1P3P & getattr(taus, f"mode{mode}")
    plots += create_res_profiles(samples, depvars=depvars, tag=mode+"LC",       sel=sel, mode="core", yvar=taus.ptRes.get_view(),           **kwres)
    plots += create_res_profiles(samples, depvars=depvars, tag=mode+"PanTau",   sel=sel, mode="core", yvar=taus.ptPanTauRes.get_view(),     **kwres)
    plots += create_res_profiles(samples, depvars=depvars, tag=mode+"Final",    sel=sel, mode="core", yvar=taus.ptFinalCalibRes.get_view(), **kwres)
    plots += create_res_profiles(samples, depvars=depvars, tag=mode+"Combined", sel=sel, mode="core", yvar=taus.ptCombinedRes.get_view(),   **kwres)
    

## Process
##========
proc = Processor()
proc.draw_plots(plots)

ofstream = OutputFileStream("canvases.root")
ofstream.write(plots)


## EOF
