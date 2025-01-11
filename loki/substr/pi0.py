# encoding: utf-8
"""
pi0.py

TODO:...

"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-12-05"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
import logging
from math import pi

from loki.core.file import OutputFileStream
from loki.core.hist import Hist, Profile, EffProfile, ResoProfile, Fit
from loki.core.sample import Sample
from loki.core.setup import setup
from loki.core.style import Style
from loki.core.plot import Plot
from loki.core.process import Processor
from loki.core.var import Var, Expr, Cuts, Container
from loki.common import samples, vars, cuts, styles
from loki.common.vars import taus
from loki.substr.plots import create_decay_mode_split_distributions
from loki.tauid.plots import create_eff_profiles


## config
#infile = "/Users/wedavey/Data/MxAOD/CalHits/mxaod_v3_100k.root"
infile = "/Users/wedavey/Data/MxAOD/CalHits/mxaod_v4_deco.root"


## vars
bins_phi       = [ 25, -pi, pi ]
#: Tau Neutral PFO container
neutrals = Container("TauNeutralParticleFlowObjects")

# neutral kinematics
neutrals.add_var("pt", "pt", "Reco Neutral PFO p_{T}", xunit="MeV")
neutrals.add_expr("ptGeV", "{0} / 1000.", [neutrals.pt], "Reco Neutral PFO p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_var("ptEM", "ptEM", "Reco Neutral PFO p_{T}", xunit="MeV")
neutrals.add_expr("ptEMGeV", "{0} / 1000.", [neutrals.ptEM], "Reco Neutral PFO EM p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)    
neutrals.add_var("eta", "eta", "Reco Neutral PFO #eta") \
    .add_view(*vars.bins_eta)
neutrals.add_var("phi", "phi", "Reco Neutral PFO #phi") \
    .add_view(*bins_phi)

# neutral calhits 
neutrals.add_var("ptCalHit", "ptCalHit", "Reco Neutral PFO CalHit p_{T}", xunit="MeV")
neutrals.add_expr("ptCalHitGeV", "{0} / 1000.", [neutrals.ptCalHit], "Reco Neutral PFO CalHit p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_var("ptCalHitCharged", "ptCalHitCharged", "Reco Neutral PFO Charged CalHit p_{T}", xunit="MeV")
neutrals.add_expr("ptCalHitChargedGeV", "{0} / 1000.", [neutrals.ptCalHitCharged], "Reco Neutral PFO Charged CalHit p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_var("ptCalHitNeutral", "ptCalHitNeutral", "Reco Neutral PFO Neutral CalHit p_{T}", xunit="MeV")
neutrals.add_expr("ptCalHitNeutralGeV", "{0} / 1000.", [neutrals.ptCalHitNeutral], "Reco Neutral PFO Neutral CalHit p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_var("ptCalHitOther", "ptCalHitOther", "Reco Neutral PFO Other CalHit p_{T}", xunit="MeV")
neutrals.add_expr("ptCalHitOtherGeV", "{0} / 1000.", [neutrals.ptCalHitOther], "Reco Neutral PFO Other CalHit p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_var("ptCluster", "ptCluster", "Reco Neutral PFO Cluster p_{T}", xunit="MeV")
neutrals.add_expr("ptClusterGeV", "{0} / 1000.", [neutrals.ptCluster], "Reco Neutral PFO Cluster p_{T}", xunit="GeV") \
    .add_view(20, 0., 100.)
neutrals.add_expr("ptNeutralFrac", "{0} / {1}", [neutrals.ptCalHitNeutral, neutrals.ptCalHit], "Reco Neutral PFO Neutral Fraction") \
    .add_view(1000,0.,1.2)
neutrals.add_expr("ptCalHitFrac", "{0} / {1}", [neutrals.ptCalHit, neutrals.ptCluster], "Reco Neutral PFO CalHit Fraction") \
    .add_view(1000,0.,2.)

# id vars
neutrals.add_var("nPi0Proto", "nPi0Proto").add_view(4, -0.5, 3.5)
neutrals.add_var("bdtPi0Score", "bdtPi0Score").add_view(20, -1.0, 1.0)

# neutral moments
neutrals.add_var("centerMag", "centerMag").add_view(20, 0, 5000)
neutrals.add_var("CENTER_LAMBDA", "cellBased_CENTER_LAMBDA").add_view(20, 0., 1000.)
neutrals.add_var("DELTA_PHI", "cellBased_DELTA_PHI").add_view(20, -3.2, 3.2)
neutrals.add_var("DELTA_THETA", "cellBased_DELTA_THETA").add_view(20, -1.0, 1.0)
neutrals.add_var("EM1CoreFrac", "cellBased_EM1CoreFrac").add_view(20, 0.0, 1.0)
neutrals.add_var("ENG_FRAC_CORE", "cellBased_ENG_FRAC_CORE").add_view(20, 0.0, 1.0)
neutrals.add_var("ENG_FRAC_EM", "cellBased_ENG_FRAC_EM").add_view(20, 0.0, 1.0)
neutrals.add_var("ENG_FRAC_MAX", "cellBased_ENG_FRAC_MAX").add_view(20, 0.0, 1.0)
neutrals.add_var("FIRST_ETA", "cellBased_FIRST_ETA").add_view(20, -3.0, 3.0)
neutrals.add_var("LATERAL", "cellBased_LATERAL").add_view(20, 0.0, 1.0)
neutrals.add_var("LONGITUDINAL", "cellBased_LONGITUDINAL").add_view(20, 0.0, 1.0)
neutrals.add_var("NHitsInEM1", "cellBased_NHitsInEM1").add_view(10, -0.5, 9.5)
neutrals.add_var("NPosECells_EM1", "cellBased_NPosECells_EM1").add_view(20, 0, 150)
neutrals.add_var("NPosECells_EM2", "cellBased_NPosECells_EM2").add_view(20, 0, 100)
neutrals.add_var("NPosECells_PS", "cellBased_NPosECells_PS").add_view(15, -0.5, 14.5)
neutrals.add_var("SECOND_ENG_DENS", "cellBased_SECOND_ENG_DENS").add_view(20, 0., 0.002)
neutrals.add_expr("logSECOND_ENG_DENS", "log({0})", [neutrals.SECOND_ENG_DENS]).add_view(20, -24, 1)
neutrals.add_var("SECOND_LAMBDA", "cellBased_SECOND_LAMBDA").add_view(20, 0, 150)
neutrals.add_var("SECOND_R", "cellBased_SECOND_R").add_view(20, 0, 40000)
neutrals.add_var("energy_EM1", "cellBased_energy_EM1").add_view(20, -5000, 45000)
neutrals.add_var("energy_EM2", "cellBased_energy_EM2").add_view(20, -5000, 95000)
neutrals.add_var("firstEtaWRTClusterPosition_EM1", "cellBased_firstEtaWRTClusterPosition_EM1").add_view(20, -0.05, 0.05)
neutrals.add_var("firstEtaWRTClusterPosition_EM2", "cellBased_firstEtaWRTClusterPosition_EM2").add_view(20, -0.03, 0.03)
neutrals.add_var("secondEtaWRTClusterPosition_EM1", "cellBased_secondEtaWRTClusterPosition_EM1").add_view(20, 0, 0.005)
neutrals.add_var("secondEtaWRTClusterPosition_EM2", "cellBased_secondEtaWRTClusterPosition_EM2").add_view(20, 0, 0.005)

neutral_kinematics = [v.get_view() for v in [neutrals.ptGeV, neutrals.ptEMGeV, neutrals.eta, neutrals.phi]]
neutral_moments = [v.get_view() for v in [\
    neutrals.centerMag, neutrals.CENTER_LAMBDA, neutrals.DELTA_PHI, 
    neutrals.DELTA_THETA, neutrals.EM1CoreFrac, neutrals.ENG_FRAC_CORE, 
    neutrals.ENG_FRAC_EM, neutrals.ENG_FRAC_MAX, neutrals.FIRST_ETA, 
    neutrals.LATERAL, neutrals.LONGITUDINAL, neutrals.NHitsInEM1, 
    neutrals.NPosECells_EM1, neutrals.NPosECells_EM2, neutrals.NPosECells_PS, 
    neutrals.logSECOND_ENG_DENS, neutrals.SECOND_LAMBDA, neutrals.SECOND_R, 
    neutrals.energy_EM1, neutrals.energy_EM2, 
    neutrals.firstEtaWRTClusterPosition_EM1, neutrals.firstEtaWRTClusterPosition_EM2, 
    neutrals.secondEtaWRTClusterPosition_EM1, neutrals.secondEtaWRTClusterPosition_EM2,
    ]]

## selection
neutrals.add_expr("isPileup", "{0} < 0.2", [neutrals.ptCalHitFrac])
neutrals.add_expr("isNeutral", "({0} > 0.7) && ({1} > 0.2)", [neutrals.ptNeutralFrac, neutrals.ptCalHitFrac])
neutrals.add_expr("isCharged", "({0} < 0.3) && ({1} > 0.2)", [neutrals.ptNeutralFrac, neutrals.ptCalHitFrac])


## styles
#sty_all  = Style("All",       LineStyle=2, LineWidth=3)
#sty_25NL = Style("Trig   !L",   FillColor=styles.black, LineColor=styles.black)
#sty_LNM  = Style("Trig+L !M", FillColor=styles.green, LineColor=styles.green)
#sty_MNT  = Style("Trig+M !T", FillColor=styles.blue,  LineColor=styles.blue)
#sty_T    = Style("Trig+T",    FillColor=styles.red,   LineColor=styles.red)

#sty_incl = Style("incl.", MarkerColor=styles.black, LineColor=styles.black, MarkerStyle=styles.fullcircle)
#sty_barrel = Style("barrel", MarkerColor=styles.red, LineColor=styles.red, MarkerStyle=styles.fulltriup)
#sty_endcap = Style("endcap", MarkerColor=styles.blue, LineColor=styles.blue, MarkerStyle=styles.fulltridn)

"""
def create_stack_plots(s, sel, var, tag):
    vname = var.var.get_name()
    h_all  = Hist(sample=s, xvar=var, sty=sty_all,  sel=sel&tau1_not25, name=f"h_{vname}_all_{tag}")
    h_25NL = Hist(sample=s, xvar=var, sty=sty_25NL, sel=sel&tau1_25NL,  name=f"h_{vname}_25NL_{tag}")
    h_LNM  = Hist(sample=s, xvar=var, sty=sty_LNM,  sel=sel&tau1_LNM,   name=f"h_{vname}_LNM_{tag}")
    h_MNT  = Hist(sample=s, xvar=var, sty=sty_MNT,  sel=sel&tau1_MNT,   name=f"h_{vname}_MNT_{tag}")
    h_T    = Hist(sample=s, xvar=var, sty=sty_T,    sel=sel&tau1_T,     name=f"h_{vname}_T_{tag}")
    p      = Plot(f"p_{vname}_{tag}",     rds=[h_all, h_25NL, h_LNM, h_MNT, h_T], ymin=0,   stack=True, extra_labels=[tag])
    p_log  = Plot(f"p_{vname}_{tag}_log", rds=[h_all, h_25NL, h_LNM, h_MNT, h_T], ymin=0.1, stack=True, logy=True, extra_labels=[tag])
    return [p, p_log]
"""


#______________________________________________________________________________=buf=
def create_var_dists(samples,vars=None,sel=None, normalize=True, dir="variables",tag=None):
    """Return list of variable distribution overlay plots
    
    :param samples: samples to overlay
    :type samples: list :class:`loki.core.sample.Sample`
    :param vars: variables to plot 
    :type vars: list :class:`loki.core.var.Var`
    :param sel: selection to apply
    :type sel: :class:`loki.core.cut.Cut` 
    :param normalize: normalize the distributions to unit area
    :type normalize: bool
    :param dir: target canvas directory for saving plots 
    :type dir: str
    :param tag: unique name tag for plots
    :type tag: str
    :rtype: list :class:`loki.core.plot.Plot`
    """  
    # make plots                    
    plots = []
    for var in vars:
        # make a hist for each sample and add to plot  
        hists = []
        for s in samples: 
            hist_name = f"{var.get_name()}{s.name}"
            if tag: 
                hist_name+=tag
            h = Hist(sample = s, name = hist_name, xvar = var, sel = sel, normalize = normalize)
            hists.append(h)
        plot_name = var.get_name()
        if tag: 
            plot_name+=tag
        plot = Plot(plot_name, hists, dir=dir, ymin=0.0)
        plots.append(plot)
        plot_log = Plot(plot_name+"_log", hists, dir=dir, logy=True)
        plots.append(plot_log)

    return plots 






# Setup loki framework
# --------------------
#setup(log_level=logging.DEBUG)
setup()

sty_neutral = Style("Neutral", LineColor=styles.red,  MarkerColor=styles.red,  MarkerStyle=styles.fullcircle)
sty_charged = Style("Charged",LineColor=styles.black,MarkerColor=styles.black,MarkerStyle=styles.fullsquare)
sty_pileup = Style("Pileup",LineColor=styles.gray,MarkerColor=styles.gray,MarkerStyle=styles.opensquare)

## Setup samples (make more general in future)
s = Sample("All", files=[infile])
sNeutral = Sample("Neutral", sty=sty_neutral, sel=neutrals.isNeutral, files=[infile])
sCharged = Sample("Charged", sty=sty_charged, sel=neutrals.isCharged, files=[infile])
sPileup = Sample("Pileup", sty=sty_pileup, sel=neutrals.isPileup, files=[infile])







plots = []


## Calibration Hit Plots
plots_calhit = []
sty_scatter = Style("scatter", MarkerColor=styles.black, MarkerStyle=1)
h_CalHit_neut_vs_tot = Hist(sample=s, sty=sty_scatter, xvar=neutrals.ptCalHitFrac.get_view(), yvar=neutrals.ptNeutralFrac.get_view())
h_CalHit_neut_vs_tot.drawopt = ""
plots_calhit += [Plot("p_CalHit_neut_vs_tot", rds=[h_CalHit_neut_vs_tot])]


## moments plots
plots_moments = create_var_dists([sNeutral,sCharged,sPileup], vars=neutral_kinematics+neutral_moments+[neutrals.bdtPi0Score.get_view()])



"""
## jet trigger plots
depvars = [tau0_pt.get_view("log"), tau1_pt.get_view("log")]
# Dont really make sense due to derivation selection
#plots += create_eff_profiles(sALL, wpdefs=trigdefs, depvars=depvars)
#plots += create_decay_mode_split_distributions(sALL, wpdefs=trigdefs_inv, tidvars=depvars)

plots_jettrig = []
plots_jettrig += create_decay_mode_split_distributions(sALL, wpdefs=trigdefs_inv, wps=triggers, tidvars=depvars, stack_normalize=True, tag="stacknorm")
plots_jettrig += create_decay_mode_split_distributions(sALL, wpdefs=trigdefs_inv, wps=triggers, tidvars=depvars)
plots_jettrig += create_decay_mode_split_distributions(sALL, wpdefs=trigdefs_inv, wps=[pstrig,npstrig], tidvars=depvars, stack_normalize=True, tag="psmerge_stacknorm")
plots_jettrig += create_decay_mode_split_distributions(sALL, wpdefs=trigdefs_inv, wps=[pstrig,npstrig], tidvars=depvars, tag="psmerge")
for p in plots_jettrig: p.ymin=0

## tau1 BDT plots
plots_bdt = []
plots_bdt += create_stack_plots(trigsamps[pstrig], tau1_1P,tau1_bdt.get_view(),"1P_pstrig") 
plots_bdt += create_stack_plots(trigsamps[pstrig], tau1_3P,tau1_bdt.get_view(),"3P_pstrig") 
plots_bdt += create_stack_plots(trigsamps[npstrig],tau1_1P,tau1_bdt.get_view(),"1P_npstrig") 
plots_bdt += create_stack_plots(trigsamps[npstrig],tau1_3P,tau1_bdt.get_view(),"3P_npstrig") 


## Fake-factor plots
depvars1 = [tau1_pt.get_view("log2"), tau1_pt.get_view("low")]
depvars1_eta = [tau1_abseta.get_view()]
sPS  = trigsamps[pstrig]
sNPS = trigsamps[npstrig] 

# trigger overlay (maybe bring back once we have enough stats)
plots_ff = []
plots_ffnojet = []
#plots_ff += create_eff_profiles([s]+trigsamps.values(), wpdefs=tiddefs1P, depvars=depvars1, wrt=False, fakes=True, prongs=1,tag="TrigOverlay")
#plots_ff += create_eff_profiles([s]+trigsamps.values(), wpdefs=tiddefs3P, depvars=depvars1, wrt=False, fakes=True, prongs=3,tag="TrigOverlay")
for id in tiddefs1P: 
    # split PS / NPS 
    plots_ff += create_eff_profiles([sPS,sNPS], wpdefs=tiddefs1P[id], depvars=depvars1+depvars1_eta,     
                wrt=False, fakes=True, prongs=1,tag=f"TrigSplit_{id}_wrt_{ffbase.get_name()}", wps=["incl"])
    # split barrel / end
    plots_ff += create_eff_profiles(sALL, wpdefs=tiddefs1P[id], depvars=depvars1, wrt=False, fakes=True, 
                prongs=1,tag=f"TrigMerge_etasplit_{id}_wrt_{ffbase.get_name()}")

    ## DODGY PLOTS WITH NO JET TRIGGERS
    plots_ffnojet += create_eff_profiles(sNOJET, wpdefs=tiddefs1P[id], depvars=depvars1, wrt=False, fakes=True, 
                prongs=1,tag=f"TrigNOJET_etasplit_{id}_wrt_{ffbase.get_name()}")


for id in tiddefs3P: 
    # split PS / NPS 
    plots_ff += create_eff_profiles([sPS,sNPS], wpdefs=tiddefs3P[id], depvars=depvars1+depvars1_eta,     
                wrt=False, fakes=True, prongs=3,tag=f"TrigSplit_{id}_wrt_{ffbase.get_name()}", wps=["incl"])
    # split barrel / end
    plots_ff += create_eff_profiles(sALL, wpdefs=tiddefs3P[id], depvars=depvars1, wrt=False, fakes=True, 
                prongs=3,tag=f"TrigMerge_etasplit_{id}_wrt_{ffbase.get_name()}")

    ## DODGY PLOTS WITH NO JET TRIGGERS
    plots_ffnojet += create_eff_profiles(sNOJET, wpdefs=tiddefs3P[id], depvars=depvars1, wrt=False, fakes=True, 
                prongs=3,tag=f"TrigNOJET_etasplit_{id}_wrt_{ffbase.get_name()}")






#for p in plots: p.ymin=0
"""

# Select Plots
# ------------
plots += plots_calhit
plots += plots_moments

# Process the plot
# ----------------
processor = Processor()  
processor.draw_plots(plots)
ofstream = OutputFileStream("canvases.root")
ofstream.write(plots)







