# encoding: utf-8
"""
loki.common.styles
~~~~~~~~~~~~~~~~~~

Definition of styles (using :class:`loki.core.style.Style`).

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-21"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"



## modules
import ROOT
from loki.core.style import Style


# - - - - - - - - - - - ROOT types - - - - - - - - - - - - #
# colors (https://root.cern.ch/doc/master/classTColor.html)
black  = ROOT.kBlack
white  = ROOT.kWhite
red    = ROOT.kRed
blue   = ROOT.kBlue
green  = ROOT.kGreen+2
magenta= ROOT.kMagenta
orange = ROOT.kOrange
cyan   = ROOT.kCyan+1
lgreen = ROOT.kGreen-8
lblue  = ROOT.kBlue-9
gray   = ROOT.kGray+1
dgray  = ROOT.kGray+3

# marker styles (https://root.cern.ch/doc/master/classTAttMarker.html)
fullcircle = ROOT.kFullCircle
fullsquare = ROOT.kFullSquare
fulltriup  = ROOT.kFullTriangleUp
fulltridn  = ROOT.kFullTriangleDown
fulldiamond= ROOT.kFullDiamond
fullstar   = ROOT.kFullStar
opencircle = ROOT.kOpenCircle
opensquare = ROOT.kOpenSquare
opentriup  = ROOT.kOpenTriangleUp
opentridn  = ROOT.kOpenTriangleDown
openstar   = ROOT.kOpenStar


# - - - - - - - - - - - style defs  - - - - - - - - - - - - #
## working points
Reco       = Style("Reco", LineColor=black,MarkerColor=black,MarkerStyle=fulldiamond,drawopt="P,E1")
Loose      = Style("Loose", LineColor=green,MarkerColor=green,MarkerStyle=fullcircle, drawopt="P,E1")
Medium     = Style("Medium",LineColor=blue, MarkerColor=blue, MarkerStyle=fulltriup,  drawopt="P,E1" )
Tight      = Style("Tight", LineColor=red,  MarkerColor=red,  MarkerStyle=fullsquare, drawopt="P,E1" )

## modes
m1P0N = Style("1P0N", tlatex="#it{h}^{#pm}"                                , LineColor=green  ,FillColor=green  ,MarkerColor=green  ,MarkerStyle=fullcircle , drawopt="P,E1")
m1P1N = Style("1P1N", tlatex="#it{h}^{#pm}#scale[0.5]{ }#it{#pi}^{0}"      , LineColor=blue   ,FillColor=blue   ,MarkerColor=blue   ,MarkerStyle=fulltriup  , drawopt="P,E1")
m1PXN = Style("1PXN", tlatex="#it{h}^{#pm}#scale[0.5]{ }#geq2#it{#pi}^{0}" , LineColor=red    ,FillColor=red    ,MarkerColor=red    ,MarkerStyle=fulltridn  , drawopt="P,E1")
m3P0N = Style("3P0N", tlatex="3#it{h}^{#pm}"                               , LineColor=magenta,FillColor=magenta,MarkerColor=magenta,MarkerStyle=fullsquare , drawopt="P,E1")
m3PXN = Style("3PXN", tlatex="3#it{h}^{#pm}#scale[0.5]{ }#geq1#it{#pi}^{0}", LineColor=orange ,FillColor=orange ,MarkerColor=orange ,MarkerStyle=fulldiamond, drawopt="P,E1")

## algs 
TESLC    = Style("TESLC"   , tlatex = "Baseline"    , LineColor=green ,FillColor=green ,MarkerColor=green ,MarkerStyle=fullcircle , drawopt="P,E1")
TESSub   = Style("TESSub"  , tlatex = "Constituent" , LineColor=blue  ,FillColor=blue  ,MarkerColor=blue  ,MarkerStyle=fulltriup  , drawopt="P,E1")
TESFinal = Style("TESFinal", tlatex = "Final"       , LineColor=red   ,FillColor=red   ,MarkerColor=red   ,MarkerStyle=fulldiamond, drawopt="P,E1")
TESComb  = Style("TESComb" , tlatex = "Combined"    , LineColor=black ,FillColor=black ,MarkerColor=black ,MarkerStyle=fulltridn  , drawopt="P,E1")

ROC1P = Style("ROC1P",tlatex="1-prong",LineColor=blue,LineWidth=3,drawopt="L")
ROC3P = Style("ROC3P",tlatex="3-prong",LineColor=red,LineWidth=3,drawopt="L")

fit = Style("fit","Fit",LineColor=red,LineWidth=2,drawopt="F")

## samples
Signal     = Style("Signal",    LineColor=red,  MarkerColor=red,  MarkerStyle=fullcircle)
Background = Style("Background",LineColor=black,MarkerColor=black,MarkerStyle=fullsquare)
SignalTrain     = Style("SignalTrain",    LineColor=red,  LineStyle=2, MarkerColor=red,  MarkerStyle=opencircle)
BackgroundTrain = Style("BackgroundTrain",LineColor=black,LineStyle=2, MarkerColor=black,MarkerStyle=opensquare)
SignalTest      = Style("SignalTest",     LineColor=red,  MarkerColor=red,  MarkerStyle=fullcircle)
BackgroundTest  = Style("BackgroundTest", LineColor=black,MarkerColor=black,MarkerStyle=fullsquare)
Target     = Style("Target",    LineColor=red,  MarkerColor=red,  MarkerStyle=opencircle)
Reference  = Style("Reference", LineColor=black,MarkerColor=black,MarkerStyle=fullcircle)
Test       = Style("Test",      LineColor=red,  MarkerColor=red,  MarkerStyle=opencircle)

## sample stack styles
Ztautau   = Style("Ztautau" ,tlatex="#it{Z}#rightarrow#it{#tau#tau}"        , FillColor=red)
DYtautau  = Style("DYtautau",tlatex="#it{Z/#gamma}*#rightarrow#it{#tau#tau}", FillColor=white,LineColor=black)
Gammatautau = Style("Gammatautau" ,tlatex="#it{#gamma*}#rightarrow#it{#tau#tau}", FillColor=white, LineColor=dgray)
DYee      = Style("DYee"    ,tlatex="#it{Z/#gamma}*#rightarrow#it{ee}"      , FillColor=orange,LineColor=orange,MarkerColor=orange,MarkerStyle=fulltriup)
Zee = DYee
DYmumu    = Style("DYmumu"  ,tlatex="#it{Z/#gamma}*#rightarrow#it{#mu#mu}"  , FillColor=orange,LineColor=orange,MarkerColor=orange,MarkerStyle=fulltriup)
Zmumu = DYmumu
Multijet  = Style("Multijet",tlatex="Multijet", FillColor=red, LineColor=red, MarkerColor=red, MarkerStyle=fullsquare)
ggH125    = Style("ggH125"  ,tlatex="#it{ggH}(125)#rightarrow#it{#tau#tau}", FillColor=blue, LineColor=blue)
VBFH125   = Style("VBFH125" ,tlatex="VBF #it{H}(125)#rightarrow#it{#tau#tau}", FillColor=magenta, LineColor=magenta)

## systematics
NOMINAL = Style("NOMINAL", tlatex="Nominal",      LineColor=black  ,FillColor=black  ,MarkerColor=black  ,MarkerStyle=fullcircle , drawopt="P,E1")
GEO1    = Style("GEO1",    tlatex="Geo 1",        LineColor=green  ,FillColor=green  ,MarkerColor=green  ,MarkerStyle=fulldiamond, drawopt="P,E1")
GEO2    = Style("GEO2",    tlatex="Geo 2",        LineColor=blue   ,FillColor=blue   ,MarkerColor=blue   ,MarkerStyle=fulltriup  , drawopt="P,E1")
PL1     = Style("PL1",     tlatex="Party List 1", LineColor=red    ,FillColor=red    ,MarkerColor=red    ,MarkerStyle=fulltridn  , drawopt="P,E1")
PL2     = Style("PL2",     tlatex="Party List 2", LineColor=magenta,FillColor=magenta,MarkerColor=magenta,MarkerStyle=fullsquare , drawopt="P,E1")
AF2     = Style("AF2",     tlatex="AF2",          LineColor=orange ,FillColor=orange ,MarkerColor=orange ,MarkerStyle=fullsquare , drawopt="P,E1")
TRT1    = Style("TRT1",    tlatex="TRT1",         LineColor=red    ,FillColor=red    ,MarkerColor=red    ,MarkerStyle=fulltriup  , drawopt="P,E1")
TRT2    = Style("TRT2",    tlatex="TRT2",         LineColor=red    ,FillColor=red    ,MarkerColor=red    ,MarkerStyle=fulltridn  , drawopt="P,E1")

TOT1    = Style("TOT1", tlatex="TOT1", LineColor=black  ,FillColor=black  ,MarkerColor=black  ,MarkerStyle=fullcircle , drawopt="P,E1")
TOT2    = Style("TOT2", tlatex="TOT2", LineColor=green  ,FillColor=green  ,MarkerColor=green  ,MarkerStyle=fulldiamond, drawopt="P,E1")
TOT3    = Style("TOT3", tlatex="TOT3", LineColor=blue   ,FillColor=blue   ,MarkerColor=blue   ,MarkerStyle=fulltriup  , drawopt="P,E1")


## un-named list of styles
style_list = [
    Style("STY01", LineColor=black  ,FillColor=black  ,MarkerColor=black  ,MarkerStyle=fullcircle , drawopt="P,E1"),
    Style("STY02", LineColor=green  ,FillColor=green  ,MarkerColor=green  ,MarkerStyle=fulldiamond, drawopt="P,E1"),
    Style("STY03", LineColor=blue   ,FillColor=blue   ,MarkerColor=blue   ,MarkerStyle=fulltriup  , drawopt="P,E1"),
    Style("STY04", LineColor=red    ,FillColor=red    ,MarkerColor=red    ,MarkerStyle=fulltridn  , drawopt="P,E1"),
    Style("STY05", LineColor=magenta,FillColor=magenta,MarkerColor=magenta,MarkerStyle=fullsquare , drawopt="P,E1"),
    Style("STY06", LineColor=orange ,FillColor=orange ,MarkerColor=orange ,MarkerStyle=opensquare , drawopt="P,E1"),
    Style("STY07", LineColor=cyan   ,FillColor=cyan   ,MarkerColor=cyan   ,MarkerStyle=opentriup  , drawopt="P,E1"),
    Style("STY08", LineColor=lgreen ,FillColor=lgreen ,MarkerColor=lgreen ,MarkerStyle=opentridn  , drawopt="P,E1"),
    Style("STY09", LineColor=gray   ,FillColor=gray   ,MarkerColor=gray   ,MarkerStyle=opencircle , drawopt="P,E1"),
    Style("STY10", LineColor=lblue  ,FillColor=lblue  ,MarkerColor=lblue  ,MarkerStyle=fulldiamond, drawopt="P,E1"),
    Style("STY11", LineColor=magenta,FillColor=lblue  ,MarkerColor=magenta,MarkerStyle=opencircle , drawopt="P,E1"),    
    ] + [Style("STY{0:d}".format(i), LineColor=i, FillColor=i, MarkerColor=i, MarkerStyle=fullstar, drawopt="P,E1") for i in range(12,40)]



## EOF
