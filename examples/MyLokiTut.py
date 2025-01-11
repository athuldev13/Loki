# setup loki first to to give you a nice printout
from loki.core.setup import setup
setup()

from loki.common import samples
from loki.core.file import FileHandler

import ROOT

# specify path to the folder where samples are stored
SamplePath = '/eos/atlas/atlascerngroupdisk/perf-tau/MxAODs/R22/Run2repro/TauID'

# define signal and background sample from precofigured loki Sample objects
signal = samples.Gammatautau
bkg = samples.Multijet

# convinient tool to associate the samples with the file paths
# it will add files to signal and bkg depending on string matches
FileHandler(SamplePath, [signal, bkg])


# import all preconfigured variables
# this will give you also access to taus, tautracks .. Containers
from loki.common.vars import *

# Now add a variable to taus container:
# taus.add_var(<name in container>, <var name in MxAODs>, <description (will be x-axis label)>)
# adding a view with .add_view(<nBins>, <xMin>, <xMax>)

taus.add_var("MyNTrackOfTaus", "nTracks", "My nTrack").add_view(5, 0, 5)

# Important Note:
# In xAODs and MxAODs information is usually present as branches of trees in this form:
# TauJetsAux.pt or TauJetsAuxDyn.nTracks
# Loki takes care to resolve the container name including the Aux and AuxDyn part
# Thus you should only name the variable name without container name

from loki.core.hist import Hist
from loki.core.style import Style

# create two histograms one for taus (hTaus) from Gammatautau sample, 
# one for QCD Jets (hJets) from Multijet sample
# plus adding some cool plotting features
hTaus = Hist(sample = signal,
             xvar   = taus.MyNTrackOfTaus.get_view(),
             sel    = None,
             normalize = True)
hTaus.sty = Style("Taus", LineColor=ROOT.kBlack,MarkerColor=ROOT.kBlack,MarkerStyle=29,drawopt="P,E1")

hJets = Hist(sample = bkg,
             xvar   = taus.MyNTrackOfTaus.get_view(),
             sel    = None,
             normalize = True)
hJets.sty = Style("QCD jets", LineColor=ROOT.kRed,MarkerColor=ROOT.kRed,MarkerStyle=20,drawopt="P,E1")


# pack the two hists in one plot and give it a name, also want to make a ratio
from loki.core.plot import Plot
plot = Plot("MyFirstPlot", [hTaus, hJets], doratio = True)

# create a new processor and run the plotting machinery :)
from loki.core.process import Processor

# to speed up things a little bit, we run only on 1% of all available events
processor = Processor(ncores=10, event_frac=0.01, usecache=False)
# note the processor expects a list of plots!
processor.draw_plots([plot])


# Now we want to introduce expressions and use them as cuts

# first define cuts on 1 and 3 prong taus
# Note:
#   the TTree::Draw() like expression is the second input
#   the expression substitutes the list given in the third argument with the brackets, just like .format does for strings
taus.add_expr("oneProngs", "{0}==1", [taus.MyNTrackOfTaus])
taus.add_expr("threeProngs", "{0}==3", [taus.MyNTrackOfTaus])

# create histograms for 1 and 3 prong reconstructred taus and merge histos again:
# dont forget to add the selection :)
hTaus1Prong = Hist(sample = signal,
                   xvar   = taus.MyNTrackOfTaus.get_view(),
                   sel    = taus.oneProngs,
                   normalize = False)
hTaus1Prong.sty = Style("1 prong taus", LineColor=ROOT.kBlack,MarkerColor=ROOT.kBlack,MarkerStyle=29,drawopt="P,E1")

hTaus3Prong = Hist(sample = signal,
                   xvar   = taus.MyNTrackOfTaus.get_view(),
                   sel    = taus.threeProngs,
                   normalize = False)
hTaus3Prong.sty = Style("3 prong taus", LineColor=ROOT.kRed,MarkerColor=ROOT.kRed,MarkerStyle=20,drawopt="P,E1")

plot = Plot("MySecondPlot", [hTaus1Prong, hTaus3Prong], doratio = False, dologos=True)

# to speed up things a little bit, we run only on 10% of all available events
# note usecache = False --> IMPORTANT 
processor = Processor(ncores=10, event_frac=0.01, usecache=False)
processor.draw_plots([plot])
