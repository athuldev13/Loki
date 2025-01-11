    # setup loki first to to give you a nice printout
from loki.core.setup import setup
setup()

from loki.common import samples
from loki.core.file import FileHandler
from loki.common.vars import *
from loki.core.hist import MigrationMatrix, EffProfile
from loki.core.style import Style
from loki.core.plot import Plot
from loki.core.process import Processor

import ROOT

# specify path to the folder where samples are stored
SamplePath = '/eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/R22/Run2repro/TauID'

# define signal and background sample from precofigured loki Sample objects
signal = samples.Gammatautau
bkg = samples.Multijet

# convinient tool to associate the samples with the file paths
# it will add files to signal and bkg depending on string matches
FileHandler(SamplePath, [signal, bkg])


# We want to define eff plots and matracies
# this time we do it a little bit more efficienct and use proper functions to configure our plots

# first define a function thjat configures a decay mode classification matrix
def create_panTau_decaymode_matrix(sample):
    # use the predefined decay mode variables 
    # these will split the taus in 7 categories depending on the number of charged and neutral pions 
    xvar = taus.decayModeTruth.get_view()    
    yvar = taus.decayMode.get_view()
    
    # create a migration matrix
    # one can select whether the Matrix should be normalized in rows or columns
    # depending on what you choose the interpretation will change     
    h = MigrationMatrix(name="MyMigrationMatrix", 
                        sample=sample, 
                        xvar=xvar, 
                        yvar=yvar, 
                        sel=None, 
                        rownorm=True)
    p = Plot("MyMigrationMatrix", [h], ymax=6)
    
    # this is only a small example. In the actuall decay mode matrix additional cuts are introduced in "sel"
    # but for simplicity we skip this now

    # if you are interested in the actual definition, look here: loki/substr/plots.py (create_matrix_plots)

    return [p]

# to plot efficiency profiles we need the predefined cuts
from loki.common import cuts
def create_tauid_eff_profile(sample):
    # eff profiles create pass/total plots, so we have to define pass and total cuts
    # here we want to plot TauID efficiencies over pt for 1prong taus
    # for the denominator we use total_cut selecting 1 prong truth taus
    total_cut = taus.baseline & taus.mode1PTruth
    # taus passing a ID point have to be reco 1 prong taus
    pass_loose_cut  = total_cut & taus.mode1P & taus.loose
    pass_medium_cut = total_cut & taus.mode1P & taus.medium
    pass_tight_cut  = total_cut & taus.mode1P & taus.tight

    # define Efficiency profiles for each WP by applying the correct
    # pass cut while total cut is always the same 
    p_loose = EffProfile(sample    = sample,
                         xvar      = taus.pt.get_view(),
                         sel_pass  = pass_loose_cut,
                         sel_total = total_cut
                        )
    p_loose.sty = Style("Loose", LineColor=ROOT.kBlack,MarkerColor=ROOT.kBlack,MarkerStyle=19,drawopt="P,E1")

    p_medium = EffProfile(sample    = sample,
                          xvar      = taus.pt.get_view(),
                          sel_pass  = pass_medium_cut,
                          sel_total = total_cut
                        )
    p_medium.sty = Style("Medium", LineColor=ROOT.kRed,MarkerColor=ROOT.kRed,MarkerStyle=19,drawopt="P,E1")

    p_tight = EffProfile(sample    = sample,
                         xvar      = taus.pt.get_view(),
                         sel_pass  = pass_tight_cut,
                         sel_total = total_cut
                        )
    p_tight.sty = Style("Tight", LineColor=ROOT.kGreen,MarkerColor=ROOT.kGreen,MarkerStyle=19,drawopt="P,E1")

    # merge everything together
    plot = Plot("MyEffProfiles", [p_loose, p_medium, p_tight], doratio = False, dologos=True)

    return [plot]


# Crank the plotting machine
# note that we fill one list with all plots :)
# note usecache = False --> IMPORTANT 
plots = []
plots += create_panTau_decaymode_matrix(signal)
plots += create_tauid_eff_profile(signal)
processor = Processor(ncores=10, event_frac=0.05, usecache=False)
processor.draw_plots(plots)
